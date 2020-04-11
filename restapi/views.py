from django.contrib.auth.models import User, Group
from .models import NewsItem, Rating
from rest_framework import viewsets
from rest_framework_extensions.mixins import NestedViewSetMixin

from restapi.serializers import UserSerializer, GroupSerializer, \
    NewsItemSerializer, RatingSerializer


class UserViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer


class GroupViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class NewsItemViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    """
    API endpoint that allows queued news items to be viewed or edited.
    """
    queryset = NewsItem.objects.all()
    serializer_class = NewsItemSerializer


class RatingViewSet(viewsets.ModelViewSet):
    serializer_class = RatingSerializer
    queryset = Rating.objects.all()

    def perform_create(self, serializer):
        # add current user if missing
        serializer.save(user=self.request.user)


class NewsItemRatingViewSet(NestedViewSetMixin, RatingViewSet):
    # when it's nested, it picks parent newsItem
    def destroy(self, request, *args, **kwargs):
        newsItem_id = self.get_parents_query_dict()['newsItem_id']
        newsItem = NewsItem.objects.get(pk=newsItem_id)
        newsItem.ratings.filter(pk=self.get_object().pk).delete()

    def create(self, request, *args, **kwargs):
        newsItem_id = self.get_parents_query_dict()['newsItem_id']
        request.data['newsItem'] = newsItem_id
        return super(NewsItemRatingViewSet, self).create(request, *args, **kwargs)
