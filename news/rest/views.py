"""
Exposed API for handling news, publicly published, restricted
by auth
"""
from typing import Any

from PIL import Image

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.http.response import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie, vary_on_headers
from django_filters.rest_framework import DjangoFilterBackend
from dogauth.permissions import (
    IsAuthenticated,
    IsOwnerOrModeratorOrStaff,
    IsOwnerOrStaff,
)
from rest_framework import (
    filters,
    mixins,
    permissions,
    viewsets,
    views,
    parsers,
    status,
)
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_field,
    extend_schema_serializer,
    OpenApiParameter,
)
from drf_spectacular.types import OpenApiTypes

from ..models import User, Retrieval, Moderation, Submission, Vote
from .serializers import (
    ArticleSerializer,
    RetrievalSerializer,
    RetrievalThumbnailImageSerializer,
    GroupSerializer,
    ModerationSerializer,
    SubmissionSerializer,
    UserSerializer,
    VoteSerializer,
)

# pylint: disable=missing-class-docstring


# --------------------------


class UserViewSet(
    mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    queryset = get_user_model().objects.filter(is_staff=True).order_by("-date_joined")
    serializer_class = UserSerializer


class GroupViewSet(
    mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    queryset = Group.objects.filter(name__startswith="news_")
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
        "retrieval": ["isnull"],
        "retrieval__status": ["exact", "isnull"],
        "analysis__status": ["exact", "isnull"],
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


class RetrievalViewSet(viewsets.ModelViewSet):
    """
    Retrieve results attached to a submission
    """

    parser_classes = [
        parsers.MultiPartParser,
        parsers.FormParser,
        parsers.JSONParser,
        parsers.FileUploadParser,
    ]
    permission_classes = [
        IsAuthenticated,
        IsOwnerOrStaff,
        permissions.DjangoModelPermissions,
    ]

    queryset = Retrieval.objects.all()
    serializer_class = RetrievalSerializer
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    ordering_fields = ["date_created"]
    filterset_fields = ["status"]
    # parser_classes = (MultiPartParser, FormParser)

    def get_object(self):
        if "pk" not in self.kwargs:
            sub_id = self.kwargs["submission_pk"]
            submission = Submission.objects.get(id=sub_id)
            if hasattr(submission, "retrieval"):
                # since these are bots, we allow override
                pk = getattr(submission, "retrieval").pk
            else:
                submission.retrieval = Retrieval(
                    owner=self.request.user, submission=submission
                )
                submission.retrieval.save()
                pk = submission.retrieval.pk
            self.kwargs["pk"] = pk
        return super().get_object()


# special case: file uploads for thumbnails


class RetrievalThumbnailUploadView(GenericAPIView):
    """
    Uploading thumbnails. There are three thumbnail fields. You can upload as many as you need via a multipart/form-data request.

    Image format supported: png/jpg/etc.
    Maximum size:

    ## example
    ```
    PUT {{submissionUrl}}/fetch/thumbnails
    Authorization: Bearer {{JWT_ACCESS_TOKEN}}
    Content-Type: multipart/form-data;boundary="WeE843erSADF32Sdsa0329r0easfd"

    --WeE843erSADF32Sdsa0329r0easfd
    Content-Disposition: form-data; name="thumbnail_from_page"; filename="test/resources/Test-Logo-Small-Black-transparent-1.png"
    Content-type: image/png

    < ./test/resources/Test-Logo-Small-Black-transparent-1.png
    --WeE843erSADF32Sdsa0329r0easfd
    Content-Disposition: form-data; name="thumbnail_processed"; filename="test/resources/Test-Logo-Small-Black-transparent-1.png"
    Content-type: image/png

    < ./test/resources/Test-Logo-Small-Black-transparent-1.png
    --WeE843erSADF32Sdsa0329r0easfd
    ```
    """

    parser_classes = [parsers.MultiPartParser]
    permission_classes = [
        IsAuthenticated,
        IsOwnerOrStaff,
        permissions.DjangoModelPermissions,
    ]
    queryset = Retrieval.objects.all()
    serializer_class = RetrievalThumbnailImageSerializer

    def get_object(self) -> Retrieval:
        if "pk" not in self.kwargs:
            sub_id = self.kwargs["submission_pk"]
            submission = Submission.objects.get(id=sub_id)
            if hasattr(submission, "retrieval"):
                # since these are bots, we allow override
                pk = getattr(submission, "retrieval").pk
            else:
                submission.retrieval = Retrieval(
                    owner=self.request.user, submission=submission
                )
                submission.retrieval.save()
                pk = submission.retrieval.pk
            self.kwargs["pk"] = pk
        return super().get_object()

    def put(self, request, submission_pk=None, thumbnail_field=None, format=None):

        retrieval: Retrieval = self.get_object()

        # ref https://learnbatta.com/blog/parsers-in-django-rest-framework-85/

        # img = Image.open(request.data["file"])
        # request.data[thumbnail_field] = request.data["file"]
        serializer = RetrievalThumbnailImageSerializer(
            data=request.data, instance=retrieval
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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

    serializer_class = ArticleSerializer

    queryset = Submission.objects.filter(status="accepted").order_by("-date_created")

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
