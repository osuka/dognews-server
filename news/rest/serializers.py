""" Django rest framework serializers for all the entities
These transform models into various representations
"""
from collections import OrderedDict
from typing import Any
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework import serializers
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


class SubmissionSerializer(
    NonNullModelSerializer, serializers.HyperlinkedModelSerializer
):
    """A submission object that is in initial processing"""

    class Meta:
        model = Submission
        fields = [
            "url",
            "target_url",
            "status",
            "owner",
            "title",
            "description",
            "date",
            "moderation",
        ]
        read_only_fields = [
            "owner",
            "status",
            "date_created",
            "last_updated",
            "last_modified_by",
            "domain",
            "moderation",
        ]


# --------------------------------------


class ModerationSerializer(
    NonNullModelSerializer, serializers.HyperlinkedModelSerializer
):
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


class FetchSerializer(NonNullModelSerializer, serializers.HyperlinkedModelSerializer):
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


# # --------------------------------------


# class ArticleSerializer(NonNullModelSerializer):
#     class Meta:
#         model = Article
#         exclude = []

#         read_only_fields = [
#             "status",
#             "target_url",
#             "title",
#             "description",
#             "thumbnail",
#             "submitter",
#             "moderated_submission",
#             "last_updated",
#             "date_created",
#         ]
