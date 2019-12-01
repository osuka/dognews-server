''' Django rest framework serializers for all the entities
These transform models into various representations
'''
from collections import OrderedDict
from django.contrib.auth.models import User, Group
from rest_framework import serializers
from .models import NewsItem, Rating

# note on django rest framework and nulls: by default fields that are null in the DB are
# serialized as nulls. We extend the default model serializer
# not remove them

class NonNullModelSerializer(serializers.ModelSerializer):
    ''' any field that has a value of null _or_ empty string in the output json will be removed
        see discussion https://stackoverflow.com/a/45569581
    '''
    def to_representation(self, instance):
        result = super(NonNullModelSerializer, self).to_representation(instance)
        return OrderedDict([(key, result[key]) for key in result if result[key] is not None and
        result[key] != ""])

class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'groups']


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ['url', 'name']

class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        exclude = []

class RatingSerializerBrief(serializers.ModelSerializer):
    class Meta:
        model = Rating
        exclude = ['newsItem']

class NewsItemSerializer(serializers.HyperlinkedModelSerializer, NonNullModelSerializer):
    ratings = RatingSerializerBrief(many=True, required=False)
    class Meta:
        model = NewsItem
        exclude = []
