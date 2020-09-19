"""
Exposed API for handling news, publicly published, restricted
by auth
"""
from rest_framework import viewsets, permissions
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from .serializers import SubmissionSerializer, UserSerializer, GroupSerializer
from .models import Submission

# pylint: disable=missing-class-docstring

# ---------- common to be moved elsewhere


class IsAuthenticated(permissions.BasePermission):
    """Rejects all operations if the user is not authenticated."""

    def has_permission(self, request, view):
        return request.user.is_authenticated


# an example of a per-object permission
class IsOwnerOrStaff(permissions.BasePermission):
    """Allows update/partial_updated/destroy if the user is in the staff group OR if the model has
    a property called 'user' and its value equals the request user.
    Rejects all operations if the user is not authenticated.
    """

    def has_object_permission(self, request, view, obj):
        if (
            view.action == "update"
            or view.action == "partial_update"
            or view.action == "destroy"
        ):
            return obj.owner == request.user or request.user.is_staff
        return True


# --------------------------


class UserViewSet(viewsets.ModelViewSet):
    queryset = get_user_model().objects.all().order_by("-date_joined")
    serializer_class = UserSerializer


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


default_permissions = [
    IsAuthenticated,
    IsOwnerOrStaff,
    permissions.DjangoModelPermissions,
]


class SubmissionViewSet(viewsets.ModelViewSet):
    """
    Submitted articles for review
    """

    permission_classes = default_permissions
    queryset = Submission.objects.all()
    serializer_class = SubmissionSerializer

    def perform_create(self, serializer):
        # add current user if missing
        serializer.save(owner=self.request.user)
