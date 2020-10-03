"""
Exposed API for handling news, publicly published, restricted
by auth
"""
from rest_framework import viewsets, permissions, mixins
from rest_framework.exceptions import PermissionDenied, NotFound

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from dogauth.permissions import (
    IsAuthenticated,
    IsOwnerOrStaff,
    IsModeratorOrStaff,
    IsOwnerOrModeratorOrStaff,
)
from .serializers import (
    SubmissionSerializer,
    UserSerializer,
    GroupSerializer,
    ModeratedSubmissionSerializer,
    VoteSerializer,
    ArticleSerializer,
)
from .models import Submission, ModeratedSubmission, Vote, Article

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


class VoteViewSet(
    mixins.RetrieveModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet
):
    """
    Votes detail and delete. We allow a subset of functionality, the rest must go
    through /moderatedsubmission/<pk>/votes
    """

    queryset = Vote.objects.all().select_related("moderated_submission")
    serializer_class = VoteSerializer
    permission_classes = [
        IsAuthenticated,
        IsOwnerOrModeratorOrStaff,
        permissions.DjangoModelPermissions,
    ]


class ModeratedSubmissionVoteViewSet(
    mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet
):
    """
    Votes for a moderated submission - this is tied to its primary key
    that must be passed as `moderatedsubmission_pk` kwarg
    * multiple posts to the collection from same users will not create
    multiple instances, instead subsequent posts will update their vote
    """

    queryset = Vote.objects.all().select_related("moderated_submission")
    serializer_class = VoteSerializer
    permission_classes = [
        IsAuthenticated,
        IsOwnerOrModeratorOrStaff,
        permissions.DjangoModelPermissions,
    ]

    def get_queryset(self, *args, **kwargs):  # pylint: disable=unused-argument
        if "moderated_submission_pk" in self.kwargs:
            modsub_id = self.kwargs.get("moderated_submission_pk")
            return (
                super()
                .get_queryset(*args, **kwargs)
                .filter(moderated_submission_id=modsub_id)
            )
        return super().get_queryset(*args, **kwargs)

    def perform_create(self, serializer):
        if "moderated_submission_pk" in self.kwargs:
            modsub_id = self.kwargs.get("moderated_submission_pk")
            if not ModeratedSubmission.objects.filter(id=modsub_id).exists():
                raise NotFound(f"{modsub_id} does not exist")
            moderated_submission: ModeratedSubmission = ModeratedSubmission.objects.get(
                id=modsub_id
            )
            if moderated_submission.votes.filter(owner=self.request.user).exists():
                # update
                serializer.instance = moderated_submission.votes.get(
                    owner=self.request.user  # we know only one will exist
                )
                serializer.save()
            else:
                serializer.save(
                    moderated_submission_id=modsub_id, owner=self.request.user
                )
        else:
            raise NotFound("Can only add via /moderatedsubmissions endpoint")


class ArticleViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """
    Final accepted articles, read only view.
    *Public*
    """

    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = []
