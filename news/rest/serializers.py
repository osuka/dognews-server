""" Django rest framework serializers for all the entities
These transform models into various representations
"""
from collections import OrderedDict
from typing import Any, List
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField
from rest_framework.validators import UniqueValidator
from ..models import Fetch, Moderation, Submission, Vote

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


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ["url", "username", "email", "groups"]


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


class FetchSerializer(NonNullModelSerializer):
    """The result of a bot retrieving the information"""

    class Meta:
        model = Fetch

        fields = [
            "url",
            "status",
            "owner",
            "title",
            "description",
            "thumbnail",
            "generated_thumbnail",
            "thumbnail_image",
            "fetched_page",
            "last_updated",
            "date_created",
        ]
        read_only_fields = [
            "url",
            "owner",
            "last_updated",
            "date_created",
        ]


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
            "fetch",
            "moderation",
        ]
        read_only_fields = [
            "owner",
            "status",
            "date_created",
            "last_updated",
            "last_modified_by",
            "domain",
            "fetch",
            "moderation",
        ]

    fetch = FetchSerializer(required=False, allow_null=True)
    moderation = ModerationSerializer(required=False, allow_null=True)
    owner = UserSerializer(required=False)
    # fetch = serializers.SerializerMethodField(required=False)
    # moderation = serializers.SerializerMethodField(required=False)

    # def get_fetch(self, obj) -> int:
    #     return obj.fetch.pk if hasattr(obj, "fetch") else None

    # def get_moderation(self, obj) -> int:
    #     return obj.moderation.pk if hasattr(obj, "moderation") else None


# # --------------------------------------


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
    submitter = serializers.CharField(source="owner__username", read_only=True)
    approver = serializers.CharField(
        source="moderation__owner__username", read_only=True
    )

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
        return _first(
            [
                f"https://dognewsserver.gatillos.com/media/{sub.fetch.generated_thumbnail}",
                f"https://dognewsserver.gatillos.com/media/{sub.fetch.thumbnail}",
            ],
            "https://onlydognews.com/gfx/site/onlydognews-logo-main.png",
        )

    def get_description(self, sub: Submission) -> str:
        values = [sub.moderation.description, sub.fetch.description, sub.description]
        return _first(values, "")

    def get_title(self, sub: Submission) -> str:
        values = [sub.moderation.title, sub.fetch.title, sub.title]
        return _first(values, "")

    def get_target_url(self, sub: Submission) -> str:
        return _first([sub.moderation.target_url], sub.target_url)
