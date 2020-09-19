# """ Django rest framework serializers for all the entities
# These transform models into various representations
# """
# from collections import OrderedDict
# from django.contrib.auth.models import User, Group
# from rest_framework import serializers
# from rest_framework.relations import HyperlinkedIdentityField
# from .models import NewsItem, Rating


# # note on django rest framework and nulls: by default fields that are null
# # in the DB are serialized as nulls. We extend the default model serializer
# # not remove them


# class NonNullModelSerializer(serializers.ModelSerializer):
#     """ any field that has a value of null _or_ empty string in the output json
#     will be removed see discussion https://stackoverflow.com/a/45569581
#     """

#     def to_representation(self, instance):
#         result = super(NonNullModelSerializer, self).to_representation(instance)
#         return OrderedDict(
#             [
#                 (key, result[key])
#                 for key in result
#                 if result[key] is not None and result[key] != ""
#             ]
#         )


# # -------------------------------------- models that are used in the API responses/requests


# class UserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = ["url", "username", "email", "groups"]


# class GroupSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Group
#         fields = ["url", "name"]


# class RatingSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Rating
#         read_only_fields = ["user"]
#         exclude = []


# class NewsItemSerializer(
#     NonNullModelSerializer, serializers.HyperlinkedModelSerializer
# ):
#     ratings = RatingSerializer(many=True, required=False)

#     class Meta:
#         model = NewsItem
#         exclude = []

#     def create(self, validated_data):
#         # nested items have to be handled manually by default
#         ratings = validated_data.pop("ratings") if "ratings" in validated_data else []
#         instance = serializers.HyperlinkedModelSerializer.create(self, validated_data)

#         for rating_definition in ratings:
#             rating_definition.newsItem = instance
#             if "user" not in rating_definition:
#                 rating_definition["user"] = self.context["request"].user
#             rating = Rating.objects.create(**rating_definition)
#             instance.ratings.add(rating)
#             instance.save()

#         return instance
