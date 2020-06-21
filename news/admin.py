from django.contrib import admin
from django.contrib.auth.models import Permission
from . import models

from django import forms
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
import tldextract


class SavesLastModifiedByMixin:
    """ Add this to an object that has a 'last_modified_by' datetime field, and it will be
    set to the currently logged user when saving """

    def save_model(self, request, obj, form, change):
        obj.last_modified_by = request.user
        super().save_model(request, obj, form, change)


class SavesOwnerMixin:
    """ Add this to an object that has an 'owner' field that is a fk to User, and it will be set
    to the currently logged user when creating it """

    def save_model(self, request, obj, form, change):
        print("set owner mixing called")
        if not obj.pk:
            # Only set added_by during the first save.
            obj.owner = request.user
        super().save_model(request, obj, form, change)


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ["name", "codename", "content_type"]
    search_fields = [
        "name",
        "codename",
        "content_type__app_label",
        "content_type__model",
    ]
    list_filter = ["content_type__app_label", "content_type__model"]


@admin.register(models.Submission)
class SubmissionAdmin(SavesOwnerMixin, admin.ModelAdmin):
    fields = [
        "target_url",
        "title",
        "description",
        "owner",
        "status",
        "date_created",
        "last_updated",
    ]
    list_display = [
        "date_created",
        "last_updated",
        "owner",
        "title",
        "target_url",
        "status",
    ]
    date_hierarchy = "date_created"
    list_filter = ["date_created", "last_updated", "status", "owner"]
    search_fields = ["target_url", "title", "description", "owner__username"]
    readonly_fields = ["owner", "status", "date_created", "last_updated"]

    change_form_template = "news/custom_change_form.html"

    def render_change_form(
        self,
        request,
        context,
        add=False,
        change=False,
        form_url="",
        obj: models.Submission = None,
    ):
        custom_actions = {}
        if obj and obj.status == obj.Statuses.NEW:
            custom_actions["start_moderation"] = "Move to Moderation"
            custom_actions["reject"] = "Reject"
        context.update({"custom_actions": custom_actions})
        return super().render_change_form(
            request, context, add=add, change=not add, obj=obj, form_url=form_url
        )
        # super.render_change_form(request, context, add, change, form_url, obj)

    def response_change(self, request, obj: models.Submission):
        if "start_moderation" in request.POST:
            obj.move_to_moderation()
        elif "reject" in request.POST:
            obj.status = obj.Statuses.REJECTED_MODERATOR
            obj.save()
        return super().response_change(request, obj)


class VoteInline(admin.TabularInline):
    model = models.Vote
    fields = ["owner", "value", "last_updated"]
    readonly_fields = ["owner", "value", "last_updated"]
    extra = 0

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(models.ModeratedSubmission)
class ModeratedSubmissionAdmin(SavesLastModifiedByMixin, admin.ModelAdmin):
    fields = ["submission", "target_url", "title", "description", "status"]
    list_display = [
        "date_created",
        "last_updated",
        "_submission",
        "target_url",
        "title",
        "description",
        "last_modified_by",
        "status",
    ]
    list_filter = [
        "date_created",
        "last_updated",
        "status",
        "submission__owner",
        "last_modified_by",
    ]
    search_fields = [
        "target_url",
        "title",
        "description",
        "submission__owner__username",
    ]
    date_hierarchy = "date_created"
    inlines = [VoteInline]

    def _submission(self, moderated_submission: models.ModeratedSubmission):
        if moderated_submission.submission:
            submission_id = moderated_submission.submission.id
            url = reverse(
                "admin:news_moderatedsubmission_change",
                kwargs={"object_id": submission_id},
            )
            return mark_safe(
                f'<a href="{url}">{submission_id} {moderated_submission.submission.title}</a>'
            )
        return None

    def get_readonly_fields(self, request, obj=None):
        if obj:  # This is the case when obj is already created i.e. it's an edit
            return ["submission"]
        else:
            return []


@admin.register(models.Vote)
class VoteAdmin(SavesOwnerMixin, admin.ModelAdmin):
    list_display = [
        "date_created",
        "owner",
        "value",
        "_target",
    ]
    fields = ["owner", "value"]
    readonly_fields = ["last_updated"]

    def _target(self, vote: models.Vote):
        return (
            f"{vote.moderated_submission.target_url}, {vote.moderated_submission.title}"
        )

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.owner != request.user:
            return ["owner", "value"]
        else:
            return []


@admin.register(models.Article)
class ArticleAdmin(admin.ModelAdmin):
    pass

