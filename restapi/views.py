from django.contrib.auth.models import User, Group
from .models import NewsItem, Rating
from rest_framework import viewsets
from rest_framework.response import Response

from restapi.serializers import UserSerializer, GroupSerializer, \
    NewsItemSerializer, RatingSerializer


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class NewsItemViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows queued news items to be viewed or edited.
    """
    queryset = NewsItem.objects.all()
    serializer_class = NewsItemSerializer


class RatingViewSet(viewsets.ModelViewSet):
    serializer_class = RatingSerializer
    def get_queryset(self):
        return Rating.objects.filter(newsItem_id=self.kwargs['newsItem_pk'])

