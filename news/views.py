"""
Exposed API for handling news, publicly published, restricted
by auth
"""
from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from dogauth.permissions import IsAuthenticated, IsOwnerOrStaff, IsModeratorOrStaff
from .serializers import (
    SubmissionSerializer,
    UserSerializer,
    GroupSerializer,
    ModeratedSubmissionSerializer,
)
from .models import Submission, ModeratedSubmission

# pylint: disable=missing-class-docstring


# --------------------------


class UserViewSet(viewsets.ModelViewSet):
    queryset = get_user_model().objects.all().order_by("-date_joined")
    serializer_class = UserSerializer


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class SubmissionViewSet(viewsets.ModelViewSet):
    """
    Submitted articles for review
    """

    permission_classes = [
        IsAuthenticated,
        IsOwnerOrStaff,
        permissions.DjangoModelPermissions,
    ]

    queryset = Submission.objects.all()
    serializer_class = SubmissionSerializer

    def perform_create(self, serializer):
        # add current user if missing
        serializer.save(owner=self.request.user)


class ModeratedSubmissionViewSet(viewsets.ModelViewSet):
    """
    Accepted articles in moderation
    """

    permission_classes = [
        IsAuthenticated,
        IsModeratorOrStaff,
        permissions.DjangoModelPermissions,
    ]
    queryset = ModeratedSubmission.objects.all()
    serializer_class = ModeratedSubmissionSerializer

    def perform_create(self, serializer):
        # these can only be created by moving a submission
        # to moderation, not directly
        raise PermissionDenied()
