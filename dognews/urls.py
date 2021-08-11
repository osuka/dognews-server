"""dognews URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, re_path
from django.urls import include
from rest_framework.authtoken import views as authviews
from rest_framework.routers import SimpleRouter
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

# from django.contrib.auth.models import Group, Permission
from news.rest.views import (
    SubmissionViewSet,
    ModerationViewSet,
    FetchViewSet,
    SubmissionVoteViewSet,
    UserViewSet,
    VoteViewSet,
)

urlpatterns = []

# this is a router that can help with nested view lookups byt concatenating
# calls to 'register' for sub paths.
# it adds parameters with a prefix of 'parent_lookup_' to self.kwargs

# Here we define newsItem and /newsItem/ID/ratings
router = SimpleRouter(trailing_slash=False)
router.register(r"submissions", SubmissionViewSet)
router.register(r"moderations", ModerationViewSet)
router.register(r"fetchs", FetchViewSet)
# router.register(r"moderatedsubmissions", ModeratedSubmissionViewSet)
router.register(r"votes", VoteViewSet)

# .list(), .retrieve(), .create(), .update(), .partial_update(), and .destroy().
urlpatterns += [
    re_path(
        r"^submissions/(?P<submission_pk>\d+)/moderation$",
        ModerationViewSet.as_view(
            {"get": "retrieve", "put": "update", "delete": "destroy"}
        ),
    ),
    re_path(
        r"^submissions/(?P<submission_pk>\d+)/fetch$",
        FetchViewSet.as_view({"get": "retrieve", "put": "update", "delete": "destroy"}),
    ),
    re_path(
        r"^submissions/(?P<submission_pk>\d+)/votes$",
        SubmissionVoteViewSet.as_view({"get": "list", "post": "create"}),
    ),
]
# router.register(r"articles", ArticleViewSet)

router.register(r"users", UserViewSet)
# router.register(r'groups', GroupViewSet)

urlpatterns += [
    path("admin/", admin.site.urls),
]

# serve media, but only in local
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns += [
    path("", include(router.urls)),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
]

urlpatterns += [
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    # Optional UI:
    path(
        "api/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]

# For Token based authentication - this endpoint allows a user to request a token by
# sending user/password auth/login is chosen by us
#
# note: we can also do
#   ./manage.py drf_create_token <username>       (creates or retrieves)
#   ./manage.py drf_create_token -r <username>      (regenerates)
urlpatterns += [re_path(r"^auth/login", authviews.obtain_auth_token)]

# For JWT Token authentication (remember this is a playground for me, there's not really a lot of need for JWT here!)
urlpatterns += [
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
]

admin.site.site_header = "Dog News"
admin.site.site_title = "Dog News Admin Site"
admin.site.index_title = "Welcome to the Dog News Server Administration Site"

# initialise default users: TODO find a better home for this, it breaks the initial
# database creation as it prevents loading to actually populate the user table 1st time

# default_bots = [
#     ["fetcher", ["change_submission", "view_submission"]],
#     [
#         "analyzer",
#         ["change_moderatedsubmission", "view_submission", "view_moderatedsubmission"],
#     ],
# ]
# for bot in default_bots:
#     name = f"bot-{bot[0]}"
#     perms = bot[1]
#     user, _ = User.objects.get_or_create(
#         username=name, email=f"{name}@gatillos.com", is_staff=True
#     )

#     for codename in perms:
#         user.user_permissions.add(Permission.objects.get(codename=codename))
#     user.save()
