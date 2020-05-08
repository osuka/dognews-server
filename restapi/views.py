from django.contrib.auth.models import User, Group
from .models import NewsItem, Rating
from rest_framework import viewsets
from rest_framework_extensions.mixins import NestedViewSetMixin

from restapi.serializers import NewsItemSerializer, RatingSerializer


class NewsItemViewSet(viewsets.ModelViewSet):
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


class NewsItem_RatingViewSet(RatingViewSet, NestedViewSetMixin):
    """
    NestedViewSetMixin helps with 'list':
    * creates a `get_queryset()` method that filters by the parent
    * provides a helper method to retrieve parent's key, `get_parents_query_dict()`
    * this works for update, partial_update, get and destroy
    * for create we need a helper
    """

    # # aka DELETE /item/<ID>/ratings/<ID>
    # def destroy(self, request, *args, **kwargs):
    #     newsItem_id = self.get_parents_query_dict()['newsItem_id']
    #     newsItem = NewsItem.objects.get(pk=newsItem_id)
    #     newsItem.ratings.filter(pk=self.get_object().pk).delete()

    # aka POST /item/<ID>/ratings
    def create(self, request, *args, **kwargs):
        newsItem_id = self.get_parents_query_dict()["newsItem_id"]
        request.data["newsItem"] = newsItem_id
        return super().create(request, *args, **kwargs)
