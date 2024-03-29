"""
Minimal UI
"""

from django import forms
from django.contrib import admin
from django.contrib.auth.models import Permission
from django.forms.models import BaseInlineFormSet
from django.urls import reverse
from django.utils.safestring import mark_safe
from custom_admin_actions.admin import CustomActionsModelAdmin

from . import models

# pylint: disable=missing-module-docstring, missing-function-docstring, missing-class-docstring


def _preview(url):
    if not url:
        return "-"

    if not url.startswith("http"):
        url = f"/media/{url}"

    return mark_safe(
        f'<a rel="noreferrer" href="{url}"><img src="{url}" width="128px"/></a>'
    )


def link_to_submission(submission: models.Submission):
    return reverse(
        f"admin:{models.Submission._meta.app_label}_{models.Submission._meta.model_name}_change",
        args=(submission.pk,),
        current_app=admin.site.name,
    )


class _SavesRequestUserFormset(BaseInlineFormSet):
    request_user = None
    # must be overriden
    field_to_store_user = None

    def _construct_form(self, i, **kwargs):
        # we use this too store the request user on construction
        form = super()._construct_form(i, **kwargs)
        form.request_user = self.request_user
        return form

    def add_user(self, instance):
        if self.request_user:
            # if the owner is set, it is maintained - if not, it's set to current user
            if hasattr(instance, self.field_to_store_user):
                setattr(instance, self.field_to_store_user, self.request_user)
                instance.save()

    def save_new(self, form, commit=True):
        """Save and return a new model instance for the given form."""
        instance = super().save_new(form, commit)
        self.add_user(instance=instance)
        return instance


class SavesLastModifiedByFormset(_SavesRequestUserFormset):
    field_to_store_user = "last_modified_by"


class SavesOwnerFormset(_SavesRequestUserFormset):
    field_to_store_user = "owner"


class SavesRequestUserMixin:
    """Add this to an object, set the `field_to_store_user` and if there is a user in the
    current request it will stored in that field when the model is saved.
    * This works both form normal ModelAdmin and for inlines like StackedInline/TabularInline.
    * It must be the first Mixin inherited so it can override get_formset
    """

    # must be overriden
    formset = None
    field_to_store_user = None

    def save_model(self, request, obj, form, change):
        """For normal ModelAdmins, this is invoked before save"""
        if hasattr(obj, self.field_to_store_user) and not getattr(
            obj, self.field_to_store_user
        ):
            setattr(obj, self.field_to_store_user, request.user)
        super().save_model(request, obj, form, change)

    def get_formset(self, request, obj=None, **kwargs):
        """For inlines we use a combination of this hook and
        setting formset to SavesUserFormset, which
        will in turn do the save intercept"""
        formset = super().get_formset(request, obj, **kwargs)
        formset.request_user = request.user
        return formset


class SavesLastModifiedByMixin(SavesRequestUserMixin):
    formset = SavesLastModifiedByFormset
    field_to_store_user = "last_modified_by"


class SavesOwnerMixin(SavesRequestUserMixin):
    formset = SavesOwnerFormset
    field_to_store_user = "owner"


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


class RetrievalInline(SavesOwnerMixin, admin.StackedInline):
    model = models.Retrieval
    fields = (
        "status",
        "title",
        "description",
        (
            "thumbnail_submitted",
            "thumbnail_submitted_preview",
        ),
        (
            "thumbnail_processed",
            "thumbnail_processed_preview",
            "thumbnail_from_page",
            "thumbnail_from_page_preview",
        ),
        "fetched_page",
        ("last_updated", "date_created", "owner"),
    )

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = [
            "title",
            "description",
            "thumbnail",
            "thumbnail_processed",
            "thumbnail_processed_preview",
            "thumbnail_submitted_preview",
            "thumbnail_from_page_preview",
            "last_updated",
            "date_created",
            "owner",
        ]
        # staff can request to re-fetch article
        if not request.user.is_staff:
            readonly_fields += "status"
        return readonly_fields

    def thumbnail_processed_preview(self, obj: models.Retrieval):
        return _preview(obj.thumbnail_processed)

    def thumbnail_from_page_preview(self, obj: models.Retrieval):
        return _preview(obj.thumbnail_from_page)

    def thumbnail_submitted_preview(self, obj: models.Retrieval):
        try:
            # will fail if image is not there or there is a connection error
            return mark_safe(
                f"""<img src="{obj.thumbnail_submitted.url}" width="{obj.thumbnail_submitted.width}"
                height={obj.thumbnail_submitted.height} />"""
            )
        except Exception as e:
            return e.msg


class AnalysisInline(SavesOwnerMixin, admin.StackedInline):
    model = models.Analysis
    fields = (
        (
            "status",
            "sentiment",
        ),
        "summary",
        ("last_updated", "date_created", "owner"),
    )

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = [
            "summary",
            "sentiment",
            "last_updated",
            "date_created",
            "owner",
        ]
        # staff can request to re-analyse article
        if not request.user.is_staff:
            readonly_fields += "status"
        return readonly_fields


class ModerationInline(SavesOwnerMixin, admin.StackedInline):
    model = models.Moderation
    fields = (
        "status",
        "target_url",
        "title",
        "description",
        ("last_updated", "date_created", "owner"),
    )
    readonly_fields = ("last_updated", "date_created", "owner")


class VoteInline(SavesOwnerMixin, admin.TabularInline):
    model = models.Vote
    fields = (
        "date_created",
        "last_updated",
        "owner",
        "value",
    )
    readonly_fields = ("last_updated", "date_created", "owner", "value")
    extra = 0

    # we don't allow adding from here, online via api/button
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(models.Submission)
class SubmissionAdmin(SavesOwnerMixin, CustomActionsModelAdmin):
    list_display = [
        "last_updated",
        "date",
        "owner",
        "title",
        "target_url",
        "status",
        "retrieval",
        "moderation",
        "preview",
    ]
    date_hierarchy = "date_created"
    list_filter = [
        "status",
        "moderation__status",
        "retrieval__status",
        "date",
        "date_created",
        "last_updated",
        "owner",
    ]
    search_fields = ["target_url", "title", "description", "owner__username"]
    list_display_links = ["last_updated", "target_url", "title"]
    inlines = [RetrievalInline, AnalysisInline, ModerationInline, VoteInline]
    title = forms.CharField(widget=forms.Textarea(attrs={"cols": 120, "rows": 2}))
    description = forms.CharField(widget=forms.Textarea(attrs={"cols": 120, "rows": 4}))

    @admin.display(description="Moderator")
    def _moderator(self, obj: models.Submission):
        if hasattr(obj, "moderation"):
            return f"{obj.moderation.owner}"
        return "-"

    @admin.display(description="Preview")
    def preview(self, obj: models.Submission):
        retrieval: models.Retrieval = obj.retrieval
        if hasattr(obj, "retrieval"):
            return _preview(
                retrieval.thumbnail_processed
                or retrieval.thumbnail_submitted
                or retrieval.thumbnail_from_page
            )
        return "-"

    def get_readonly_fields(self, request, obj: models.Submission = None):
        readonly_fields = ["status", "date_created", "last_updated"]
        if not request.user.is_staff:
            readonly_fields += "owner"
        return readonly_fields

    # pylint: disable=too-many-arguments
    def get_custom_admin_actions(
        self,
        request,
        context,
        add=False,
        change=False,
        form_url="",
        obj=None,
    ):
        # if obj and obj.status == models.SubmissionStatuses.PENDING:
        #     return {"start_moderation": "Move to Moderation", "reject": "Reject"}
        return {}

    def custom_action_called(self, request, custom_action_code, obj=None):
        # if custom_action_code == "reject":
        # obj.reject(request.user)
        return None


# class ArticleForm(forms.ModelForm):
#     class Meta:
#         model = models.Article
#         exclude = []  # pylint: disable=modelform-uses-exclude

#     title = forms.CharField(widget=forms.Textarea(attrs={"cols": 120, "rows": 2}))
#     description = forms.CharField(widget=forms.Textarea(attrs={"cols": 120, "rows": 4}))


# @admin.register(models.Article)
# class ArticleAdmin(admin.ModelAdmin):
#     exclude = []
#     form = ArticleForm
#     list_display = [
#         "date_created",
#         "last_updated",
#         "title",
#         "description",
#         "target_url",
#         "submitter",
#         "_votes",
#     ]
#     list_filter = [
#         "date_created",
#         "last_updated",
#         "submitter",
#         "moderated_submission__owner",
#     ]
#     readonly_fields = [
#         "thumbnail_preview",
#         "thumbnail",
#         "submitter_preview",
#         "submitter",
#         "moderated_submission",
#         "_moderated_submission",
#         "last_updated",
#         "date_created",
#     ]
#     ordering = ["-date_created"]

#     def thumbnail_preview(self, obj):
#         url = f"https://onlydognews.com{obj.thumbnail}"
#         return mark_safe(f'<a href="{url}"><img src="{url}" width="128px"/></a>')

#     def submitter_preview(self, obj):
#         url = f"https://onlydognews.com/gfx/site/{obj.submitter}-logo.png"
#         return mark_safe(f'<a href="{url}"><img src="{url}" width="128px"/></a>')

#     def _moderated_submission(self, article: models.Article):
#         if article.moderated_submission:
#             url = link_to_moderated_submission(article.moderated_submission)
#             return mark_safe(f'<a href="{url}">{article.moderated_submission}</a>')
#         return None

#     def _votes(self, article: models.Article):
#         votes = []
#         if article.moderated_submission:
#             votes = [
#                 models.Vote.Values(vote.value).label
#                 for vote in article.moderated_submission.votes.all()
#             ]
#         return mark_safe(
#             f'<a href="{link_to_moderated_submission(article.moderated_submission)}">{"".join(votes)}</a>'
#         )
