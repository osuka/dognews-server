""" Django rest framework serializers for all the entities
These transform models into various representations
"""
from collections import OrderedDict
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework import serializers
from .models import Submission, ModeratedSubmission, Vote

# pylint: disable=missing-class-docstring

# note on django rest framework and nulls: by default fields that are null
# in the DB are serialized as nulls. We extend the default model serializer
# not remove them


class NonNullModelSerializer(serializers.ModelSerializer):
    """any field that has a value of null _or_ empty string in the output json
    will be removed see discussion https://stackoverflow.com/a/45569581
    """

    def to_representation(self, instance):
        result = super().to_representation(instance)
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
    class Meta:
        model = Submission
        exclude = []
        read_only_fields = [
            "owner",
            "status",
            "date_created",
            "last_updated",
            "fetched_page",
            "domain",
        ]


# --------------------------------------


class ModeratedSubmissionSerializer(
    NonNullModelSerializer, serializers.HyperlinkedModelSerializer
):
    class Meta:
        model = ModeratedSubmission
        exclude = []
        read_only_fields = [
            "submission",
            "last_modified_by",
            "status",
            "date_created",
            "last_updated",
            "submission",
            "fetched_page",
            "domain",
            "bot_title",
            "bot_description",
            "bot_summary",
            "bot_sentiment",
            "bot_thumbnail",
        ]


class VoteSerializer(NonNullModelSerializer):
    """Votes are provided in Lists and don't link back to their
    submissions once serialized"""

    class Meta:
        model = Vote
        fields = [
            "value",
            "owner",
            "date_created",
            "last_updated",
        ]
        read_only_fields = [
            "owner",
            "date_created",
            "last_updated",
        ]
