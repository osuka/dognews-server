"""
Minimal UI
"""

from django import forms
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.http import HttpResponseRedirect
from django.contrib import admin
from django.contrib.admin.models import LogEntry, ContentType, CHANGE
from django.contrib.auth.models import Permission
from custom_admin_actions.admin import CustomActionsModelAdmin
from . import models

# pylint: disable=missing-module-docstring, missing-function-docstring, missing-class-docstring


def link_to_moderated_submission(moderated_submission: models.ModeratedSubmission):
    if not moderated_submission:
        return ""
    return reverse(
        "admin:%s_%s_change"
        % (
            models.ModeratedSubmission._meta.app_label,
            models.ModeratedSubmission._meta.model_name,
        ),
        args=(moderated_submission.pk,),
        current_app=admin.site.name,
    )


def link_to_submission(submission: models.Submission):
    return reverse(
        "admin:%s_%s_change"
        % (
            models.Submission._meta.app_label,
            models.Submission._meta.model_name,
        ),
        args=(submission.pk,),
        current_app=admin.site.name,
    )


def link_to_article(article: models.Article):
    return reverse(
        "admin:%s_%s_change"
        % (
            models.Article._meta.app_label,
            models.Article._meta.model_name,
        ),
        args=(article.pk,),
        current_app=admin.site.name,
    )


class SavesLastModifiedByMixin:
    """Add this to an object that has a 'last_modified_by' datetime field, and it will be
    set to the currently logged user when saving"""

    def save_model(self, request, obj, form, change):
        obj.last_modified_by = request.user
        super().save_model(request, obj, form, change)


class SavesOwnerMixin:
    """Add this to an object that has an 'owner' field that is a fk to User, and it will be set
    to the currently logged user when creating it"""

    def save_model(self, request, obj, form, change):
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
class SubmissionAdmin(SavesOwnerMixin, CustomActionsModelAdmin):
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

    def get_custom_admin_actions(
        self,
        request,
        context,
        add=False,
        change=False,
        form_url="",
        obj=None,
    ):
        if obj and obj.status == obj.Statuses.NEW:
            return {"start_moderation": "Move to Moderation", "reject": "Reject"}
        return {}

    def custom_action_called(self, request, custom_action_code, obj=None):
        if custom_action_code == "start_moderation":
            moderated_submission = obj.move_to_moderation()
            # redirect to hte ModeratedSubmission page for editing
            redirect_url = link_to_moderated_submission(moderated_submission)
            # log it into the django admin history
            LogEntry.objects.log_action(
                user_id=request.user.pk,
                content_type_id=ContentType.objects.get_for_model(
                    moderated_submission
                ).pk,
                object_id=moderated_submission.pk,
                object_repr=str(moderated_submission),
                action_flag=CHANGE,
                change_message=custom_action_code,
            )
            return HttpResponseRedirect(redirect_url)

        elif custom_action_code == "reject":
            obj.status = obj.Statuses.REJECTED_MODERATOR
            obj.save()
            return None


class VoteInline(admin.TabularInline):
    model = models.Vote
    fields = ["owner", "value", "last_updated"]
    readonly_fields = ["owner", "value", "last_updated"]
    extra = 0

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(models.ModeratedSubmission)
class ModeratedSubmissionAdmin(SavesLastModifiedByMixin, CustomActionsModelAdmin):
    fields = [
        "submission",
        "_submission",
        "target_url",
        "title",
        "description",
        "status",
    ]
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
            url = link_to_submission(moderated_submission.submission)
            return mark_safe(f'<a href="{url}">{moderated_submission.submission}</a>')
        return None

    _submission.short_description = "Submission link"

    def get_readonly_fields(self, request, obj=None):
        if obj:  # This is the case when obj is already created i.e. it's an edit
            return ["_submission", "submission"]
        else:
            return [
                "_submission",
            ]

    def get_custom_admin_actions(
        self,
        request,
        context,
        add=False,
        change=False,
        form_url="",
        obj=None,
    ):
        if obj and obj.status == obj.Statuses.NEW:
            return {"publish": "Publish as article"}
        return {}

    def custom_action_called(self, request, custom_action_code, obj=None):
        if custom_action_code == "publish":
            article = obj.move_to_article()
            # redirect to hte ModeratedSubmission page for editing
            redirect_url = link_to_article(article)
            # log it into the django admin history
            LogEntry.objects.log_action(
                user_id=request.user.pk,
                content_type_id=ContentType.objects.get_for_model(article).pk,
                object_id=article.pk,
                object_repr=str(article),
                action_flag=CHANGE,
                change_message=custom_action_code,
            )
            return HttpResponseRedirect(redirect_url)

        elif custom_action_code == "reject":
            obj.status = obj.Statuses.REJECTED_MODERATOR
            obj.save()
            return None


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


class ArticleForm(forms.ModelForm):
    class Meta:
        model = models.Article
        exclude = []  # pylint: disable=modelform-uses-exclude

    title = forms.CharField(widget=forms.Textarea(attrs={"cols": 120, "rows": 2}))
    description = forms.CharField(widget=forms.Textarea(attrs={"cols": 120, "rows": 4}))


@admin.register(models.Article)
class ArticleAdmin(admin.ModelAdmin):
    exclude = []
    form = ArticleForm
    list_display = [
        "date_created",
        "last_updated",
        "title",
        "description",
        "target_url",
        "submitter",
        "_votes",
    ]
    list_filter = [
        "date_created",
        "last_updated",
        "submitter",
        "moderated_submission__last_modified_by",
    ]
    readonly_fields = [
        "thumbnail_preview",
        "thumbnail",
        "submitter_preview",
        "submitter",
        "moderated_submission",
        "last_updated",
        "date_created",
    ]
    ordering = ["-date_created"]

    def thumbnail_preview(self, obj):
        url = f"https://onlydognews.com{obj.thumbnail}"
        return mark_safe(f'<a href="{url}"><img src="{url}" width="128px"/></a>')

    def submitter_preview(self, obj):
        url = f"https://onlydognews.com/gfx/site/{obj.submitter}-logo.png"
        return mark_safe(f'<a href="{url}"><img src="{url}" width="128px"/></a>')

    def _votes(self, article: models.Article):
        votes = []
        if article.moderated_submission:
            votes = [
                models.Vote.Values(vote.value).label
                for vote in article.moderated_submission.votes.all()
            ]
        return mark_safe(
            f'<a href="{link_to_moderated_submission(article.moderated_submission)}">{"".join(votes)}</a>'
        )
