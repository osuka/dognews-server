""" Django rest framework serializers for all the entities
These transform models into various representations
"""
from collections import OrderedDict
from dogauth.models import User
from typing import Any, List
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField
from rest_framework.validators import UniqueValidator
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_field,
    extend_schema_serializer,
)
from drf_spectacular.types import OpenApiTypes
from dogauth import permissions
from ..models import Retrieval, Moderation, Submission, Vote

# pylint: disable=missing-class-docstring

# note on django rest framework and nulls: by default fields that are null
# in the DB are serialized as nulls. We extend the default model serializer
# not remove them


class NonNullModelSerializer(serializers.ModelSerializer):
    """Any field that has a value of null _or_ empty string in the output json
    will be removed
    """

    def to_representation(self, instance):
        result = super().to_representation(instance)
        #  see discussion https://stackoverflow.com/a/45569581
        return OrderedDict(
            [
                (key, result[key])
                for key in result
                if result[key] is not None and result[key] != ""
            ]
        )


# --------------------------------------


def _username_masking_admins(user: User) -> str:
    """Helper that hides some information we don't
    want to show externally about users"""
    if not user or user.is_superuser:
        return "admin"
    return user.username


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ["id", "username", "groups"]

    username = serializers.SerializerMethodField()
    groups = serializers.SerializerMethodField()

    def get_username(self, user: User) -> str:
        # we fake an 'admin' user given to all superusers
        return _username_masking_admins(user)

    def get_groups(self, user: User) -> List[str]:
        # we fake an 'admin' group
        groups = [g.name for g in user.groups.all()]
        if user.is_superuser:
            return groups + ["admin"]
        return groups


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ["url", "name"]


# class RatingSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Rating
#         read_only_fields = ["user"]
#         exclude = []


# --------------------------------------


class ModerationSerializer(NonNullModelSerializer):
    """A human evaluation of a submission"""

    class Meta:
        model = Moderation

        fields = [
            "url",
            "target_url",
            "status",
            "owner",
            "title",
            "description",
            "last_updated",
            "date_created",
        ]
        read_only_fields = [
            "url",
            "target_url",
            "owner",
            "title",
            "description",
            "last_updated",
            "date_created",
        ]


# --------------------------------------


class RetrievalSerializer(NonNullModelSerializer):
    """The result of a bot retrieving the information"""

    class Meta:
        model = Retrieval

        fields = [
            "url",
            "status",
            "owner",
            "title",
            "description",
            "thumbnail",
            "fetched_page",
            "last_updated",
            "date_created",
            "thumbnail_from_page",
            "thumbnail_submitted",
            "thumbnail_processed",
        ]
        read_only_fields = [
            "thumbnail_from_page",
            "thumbnail_submitted",
            "thumbnail_processed",
            "url",
            "owner",
            "last_updated",
            "date_created",
        ]

    thumbnail = serializers.SerializerMethodField()

    # https://drf-spectacular.readthedocs.io/en/latest/customization.html#step-3-extend-schema-field-and-type-hints
    @extend_schema_field(
        {
            "type": "string",
            "example": "https://s3.amazonaws.com/xxxx/env/name.png?xxx&yyy",
        }
    )
    def get_thumbnail(self, obj: Retrieval):
        """return the most specific thumbnail available: the one parsed by the system,
        the one submitted by the user or the one extracted from the page - depending on
        the state of the submission."""
        return (
            obj.thumbnail_processed
            or obj.thumbnail_submitted
            or obj.thumbnail_from_page
        )


class RetrievalThumbnailImageSerializer(serializers.ModelSerializer):
    """The normal serializer can be used for FormUpload but for API upload
    we enable this one that can expose only the image as separate endpoint"""

    class Meta:
        model = Retrieval
        fields = ["thumbnail_from_page", "thumbnail_submitted", "thumbnail_processed"]

    def validate(self, attrs: Any) -> Any:

        if not any(x in attrs for x in self.Meta.fields):
            raise serializers.ValidationError(
                f"One of {self.Meta.fields} must be provided as a multipart form-data"
            )
        return super().validate(attrs)

    def save(self, *args, **kwargs):
        # if self.instance.thumbnail_image:
        #     self.instance.thumbnail_image.delete()
        return super().save(*args, **kwargs)


# --------------------------------------


class VoteSerializer(NonNullModelSerializer):
    """Votes are provided in Lists and don't link back to their
    submissions once serialized"""

    class Meta:
        model = Vote
        exclude = []
        read_only_fields = [
            "owner",
            "date_created",
            "last_updated",
        ]

    # list of fields changes based on permissions
    def get_fields(self, *args, **kwargs):
        fields = super().get_fields(*args, **kwargs)
        request = self.context.get("request")
        if request:
            user = request.user
            if not permissions.is_moderator(request):
                # TODO: can we do this also if it's not the owner?
                fields.pop("owner", None)
                fields.pop("submission", None)
                fields.pop("date_created", None)
                fields.pop("last_updated", None)
                fields.pop("id", None)
        return fields


# --------------------------------------


class SubmissionSerializer(
    NonNullModelSerializer, serializers.HyperlinkedModelSerializer
):
    """A submission object that is in initial processing"""

    class Meta:
        model = Submission
        fields = [
            "id",
            "url",
            "target_url",
            "status",
            "owner",
            "title",
            "description",
            "date",
            "retrieval",
            "moderation",
            "votes",
        ]
        read_only_fields = [
            "owner",
            "status",
            "date_created",
            "last_updated",
            "last_modified_by",
            "domain",
            "retrieval",
            "moderation",
        ]

    url = serializers.HyperlinkedIdentityField(
        view_name="submission-detail", lookup_field="pk"
    )
    retrieval = RetrievalSerializer(required=False, allow_null=True)
    moderation = ModerationSerializer(required=False, allow_null=True)
    owner = serializers.HyperlinkedRelatedField(view_name="user-detail", read_only=True)
    votes = serializers.ListSerializer(
        child=VoteSerializer(), required=False, allow_empty=True, allow_null=True
    )


# --------------------------------------


def _first(elements: List[str], defvalue: str) -> str:
    """Returns the first element that is not none.
    If all are none returns the default provided"""
    l = [x for x in elements if x]
    if len(l):
        return l[0]
    return defvalue


class ArticleSerializer(NonNullModelSerializer):
    """An article is an approved submission and it takes the title
    and description from either the automated bots or the moderation,
    if the moderator entered any"""

    thumbnail = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    submitter = serializers.SerializerMethodField()
    approver = serializers.SerializerMethodField()
    # submitter = serializers.CharField(source="owner__username", read_only=True)
    # approver = serializers.CharField(
    #     source="moderation__owner__username", read_only=True
    # )

    class Meta:
        model = Submission

        fields = read_only_fields = [
            "url",
            "status",
            "target_url",
            "title",
            "description",
            "thumbnail",
            "last_updated",
            "date_created",
            "submitter",
            # "moderated_submission",
            "approver",
        ]

    def get_thumbnail(self, sub: Submission) -> str:
        retrieval: Retrieval = sub.retrieval
        return _first(
            [
                retrieval.thumbnail_processed,
                retrieval.thumbnail_submitted,
                retrieval.thumbnail_from_page,
            ],
            "https://onlydognews.com/gfx/site/onlydognews-logo-main.png",
        )

    def get_description(self, sub: Submission) -> str:
        values = [
            sub.moderation.description,
            sub.retrieval.description,
            sub.description,
        ]
        return _first(values, "")

    def get_title(self, sub: Submission) -> str:
        values = [sub.moderation.title, sub.retrieval.title, sub.title]
        return _first(values, "")

    def get_target_url(self, sub: Submission) -> str:
        return _first([sub.moderation.target_url], sub.target_url)

    def get_submitter(self, sub: Submission) -> str:
        return _username_masking_admins(sub.owner)

    def get_approver(self, sub: Submission) -> str:
        if hasattr(sub, "moderation"):
            return _username_masking_admins(sub.moderation.owner)
        else:
            return _username_masking_admins(None)
