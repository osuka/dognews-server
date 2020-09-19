# from django.contrib.auth.models import User, Group
# from django.contrib.auth.decorators import login_required
# from .models import NewsItem, Rating
# from rest_framework import viewsets, status, permissions
# from rest_framework.response import Response

# from rest_framework_extensions.mixins import NestedViewSetMixin

# from restapi.serializers import NewsItemSerializer, RatingSerializer

# class NewsItemViewSet(viewsets.ModelViewSet):
#     """
#     API endpoint that allows queued news items to be viewed or edited.
#     """

#     queryset = NewsItem.objects.all()
#     serializer_class = NewsItemSerializer

# class IsAuthenticated(permissions.BasePermission):
#     """ Rejects all operations if the user is not authenticated.
#     """
#     def has_permission(self, request, view):
#         return request.user.is_authenticated

# # an example of a per-object permission
# class IsOwnerOrStaff(permissions.BasePermission):
#     """ Allows update/partial_updated/destroy if the user is in the staff group OR if the model has
#     a property called 'user' and its value equals the request user.
#     Rejects all operations if the user is not authenticated.
#     """
#     def has_object_permission(self, request, view, obj):
#         if view.action == 'update' or view.action == 'partial_update' or view.action == 'destroy':
#             return obj.user == request.user or request.user.is_staff
#         return True

# class RatingViewSet(viewsets.ModelViewSet):
#     serializer_class = RatingSerializer
#     queryset = Rating.objects.all()
#     permission_classes = (IsAuthenticated, IsOwnerOrStaff,)

#     def perform_create(self, serializer):
#         # add current user if missing
#         serializer.save(user=self.request.user)


# class NewsItem_RatingViewSet(RatingViewSet, NestedViewSetMixin):

#     # NestedViewSetMixin helps with 'list':
#     # * creates a `get_queryset()` method that filters by the parent
#     # * provides a helper method to retrieve parent's key, `get_parents_query_dict()`
#     # * this works for update, partial_update, get and destroy
#     # * for create we need a helper

#     # aka POST /item/<ID>/ratings
#     # we allow to use POST for updating your user's own rating too
#     def create(self, request, *args, **kwargs):
#         """
#         Create **or Update** a rating.
#         * a user can only create a rating for themselves
#         * if a rating for that user already exists, the new rating replaces previous
#         * admin users can add and update any ratings

#         Updating is allowed here as a shortcut to put/patch for when the newsItem_rating pk
#         is unknown (a common case)
#         """
#         newsItem_id = self.get_parents_query_dict()["newsItem_id"]
#         request.data["newsItem"] = newsItem_id
#         try:
#             newsItem = NewsItem.objects.get(pk=newsItem_id)
#             for rating in newsItem.ratings.all():
#                 if rating.user == request.user:
#                     self.kwargs[self.lookup_field] = rating.id
#                     return super().partial_update(request, *args, **kwargs)
#         except:
#             pass
#         # default to create unless we found it already
#         return super().create(request, *args, **kwargs)
