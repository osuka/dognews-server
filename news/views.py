"""
Exposed API for handling news, publicly published, restricted
by auth
"""
from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied, NotFound
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from dogauth.permissions import IsAuthenticated, IsOwnerOrStaff, IsModeratorOrStaff
from .serializers import (
    SubmissionSerializer,
    UserSerializer,
    GroupSerializer,
    ModeratedSubmissionSerializer,
    VoteSerializer,
)
from .models import Submission, ModeratedSubmission, Vote

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


class VoteViewSet(viewsets.ModelViewSet):
    """
    Votes for a moderated submission - this is tied to its primary key
    that must be passed as `moderatedsubmission_pk` kwarg
    Voting is offered in a very narrow way, not really suitable for a Viewset:
    * multiple posts from same users will update their vote
    * no id back to submissions is returned for votes
    """

    # the queryset is narrowed down, it doesn't cover all
    queryset = Vote.objects.all().select_related("moderated_submission")
    # queryset = Vote.objects.all()
    serializer_class = VoteSerializer
    permission_classes = [
        IsAuthenticated,
        IsModeratorOrStaff,
        permissions.DjangoModelPermissions,
    ]

    def get_queryset(self, *args, **kwargs):  # pylint: disable=unused-argument
        moderated_submission_id = self.kwargs.get("moderatedsubmission_pk")
        try:
            moderated_submission = ModeratedSubmission.objects.get(
                id=moderated_submission_id
            )
        except ModeratedSubmission.DoesNotExist as does_not_exist:
            raise NotFound(
                "The provided submission id does not exist"
            ) from does_not_exist
        return self.queryset.filter(moderated_submission=moderated_submission).order_by(
            "last_updated"
        )

    def perform_create(self, serializer):
        # we have a custom behaviour where a "double post" simply updates the previous
        moderated_submission_id = self.kwargs.get("moderatedsubmission_pk")
        try:
            moderated_submission = ModeratedSubmission.objects.get(
                id=moderated_submission_id
            )
            moderated_submission.vote(self.request.user, serializer.data["value"])
        except ModeratedSubmission.DoesNotExist as does_not_exist:
            raise NotFound(
                "The provided submission id does not exist"
            ) from does_not_exist
        return self.queryset.filter(moderated_submission=moderated_submission)
