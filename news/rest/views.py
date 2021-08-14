"""
Exposed API for handling news, publicly published, restricted
by auth
"""
from typing import Any
from rest_framework import views, viewsets, permissions, mixins
from rest_framework import generics, filters, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, NotFound, ValidationError
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie, vary_on_headers
from django_filters.rest_framework import DjangoFilterBackend

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from dogauth.permissions import (
    IsAuthenticated,
    IsOwnerOrStaff,
    IsModeratorOrStaff,
    IsOwnerOrModeratorOrStaff,
)
from .serializers import (
    ArticleSerializer,
    ModerationSerializer,
    SubmissionSerializer,
    FetchSerializer,
    VoteSerializer,
    UserSerializer,
    GroupSerializer,
)
from ..models import Fetch, Moderation, Submission, Vote

# pylint: disable=missing-class-docstring


# --------------------------


class UserViewSet(viewsets.ModelViewSet):
    queryset = get_user_model().objects.all().order_by("-date_joined")
    serializer_class = UserSerializer


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


# ---------------------------


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

    def get_queryset(self):
        """
        Returns submissions for the calling user - or if the user is a moderator,
        or staff or an admin then it returns for all users
        """
        user = self.request.user
        if (
            user.is_staff
            or user.is_superuser
            or user.has_perm(
                f"{Moderation._meta.app_label}.view_{Moderation._meta.model_name}"
            )
        ):
            return Submission.objects.all()
        return Submission.objects.filter(owner=user)

    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    # Allow /submissions?ordering=date_created
    ordering_fields = ["date_created"]
    # Allow /submissions?status=pending  for example
    filterset_fields = {
        "status": ["exact"],
        "moderation": ["isnull"],
        "moderation__status": ["exact", "isnull"],
        "fetch": ["isnull"],
        "fetch__status": ["exact", "isnull"],
        "analysis__status": ["exact", "isnull"],
        "fetch__generated_thumbnail": ["isnull"],
        "fetch__thumbnail": ["isnull"],
    }

    def perform_create(self, serializer):
        # add current user if missing
        serializer.save(owner=self.request.user)

    def perform_update(self, serializer) -> None:
        return super().perform_update(serializer)


# ---------------------------


class ModerationViewSet(viewsets.ModelViewSet):
    """
    Moderation attached to a submission
    """

    permission_classes = [
        IsAuthenticated,
        IsOwnerOrStaff,
        permissions.DjangoModelPermissions,
    ]

    queryset = Moderation.objects.all()
    serializer_class = ModerationSerializer

    def get_queryset(self):
        """
        Returns submissions for the calling user - or if the user is a moderator
        them it returns for all users
        """
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Moderation.objects.all()
        return Moderation.objects.filter(owner=user)

    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    # Allow /submissions?ordering=date_created
    ordering_fields = ["date_created"]
    # Allow /submissions?status=pending  for example
    filterset_fields = ["status"]

    def get_object(self):
        # This view can be used standalone, providing a pk /moderations/23
        # directly, or via a nested ref like /submissions/1/moderation
        if "pk" not in self.kwargs:
            sub_id = self.kwargs["submission_pk"]
            submission = Submission.objects.get(id=sub_id)
            if hasattr(submission, "moderation"):
                mod: Moderation = getattr(submission, "moderation")
                pk = mod.pk
                if mod.owner and mod.owner != self.request.user:
                    raise ValidationError(f"Object already moderated by {mod.owner}")
            else:
                pk = submission.moderation = Moderation(
                    owner=self.request.user, submission=submission
                )
                submission.moderation.save()
            self.kwargs["pk"] = pk
        return super().get_object()


class FetchViewSet(viewsets.ModelViewSet):
    """
    SFetching results attached to a submission
    """

    permission_classes = [
        IsAuthenticated,
        IsOwnerOrStaff,
        permissions.DjangoModelPermissions,
    ]

    queryset = Fetch.objects.all()
    serializer_class = FetchSerializer
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    ordering_fields = ["date_created"]
    filterset_fields = ["status"]

    def get_object(self):
        if "pk" not in self.kwargs:
            sub_id = self.kwargs["submission_pk"]
            submission = Submission.objects.get(id=sub_id)
            if hasattr(submission, "fetch"):
                # since these are bots, we allow override
                pk = getattr(submission, "fetch").pk
            else:
                submission.fetch = Fetch(owner=self.request.user, submission=submission)
                submission.fetch.save()
                pk = submission.fetch.pk
            self.kwargs["pk"] = pk
        return super().get_object()


class VoteViewSet(
    mixins.RetrieveModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet
):
    """
    Vote management, through /votes (put, patch, destroy) or through
    """

    queryset = Vote.objects.all().select_related("submission").order_by("-date_created")
    serializer_class = VoteSerializer
    permission_classes = [
        IsAuthenticated,
        IsOwnerOrModeratorOrStaff,
        permissions.DjangoModelPermissions,
    ]


class SubmissionVoteViewSet(
    mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet
):
    """
    Vote management /submissions/(id)/votes (get, post)
    """

    queryset = Vote.objects.all().select_related("submission").order_by("-date_created")
    serializer_class = VoteSerializer
    permission_classes = [
        IsAuthenticated,
        IsOwnerOrModeratorOrStaff,
        permissions.DjangoModelPermissions,
    ]

    def perform_create(self, serializer):
        if "submission_pk" in self.kwargs:
            sub_id = self.kwargs.get("submission_pk")
            if not Submission.objects.filter(id=sub_id).exists():
                raise NotFound(f"{sub_id} does not exist")
            submission: Submission = Submission.objects.get(id=sub_id)
            if submission.votes.filter(owner=self.request.user).exists():
                # update
                serializer.instance = submission.votes.get(
                    owner=self.request.user  # we know only one will exist
                )
                serializer.save()
            else:
                serializer.save(submission_id=sub_id, owner=self.request.user)


class ArticleViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """
    Final accepted articles, read only view.
    *Public*
    """

    queryset = Submission.objects.filter(status="accepted").order_by("-date_created")
    serializer_class = ArticleSerializer
    permission_classes = []

    @method_decorator(cache_page(60 * 2))
    @method_decorator(vary_on_cookie)
    @method_decorator(
        vary_on_headers(
            "Authorization",
        )
    )
    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().list(request, *args, **kwargs)

    @method_decorator(cache_page(60 * 2))
    @method_decorator(vary_on_cookie)
    @method_decorator(
        vary_on_headers(
            "Authorization",
        )
    )
    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().retrieve(request, *args, **kwargs)
