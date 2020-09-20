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
from django.contrib import admin
from django.urls import path
from django.urls import include
from django.conf.urls import url
from rest_framework import permissions
from rest_framework.authtoken import views as authviews
from rest_framework_extensions.routers import ExtendedDefaultRouter
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

# from django.contrib.auth.models import Group, Permission
from news.views import SubmissionViewSet, UserViewSet, ModeratedSubmissionViewSet


# this is a router that can help with nested view lookups byt concatenating
# calls to 'register' for sub paths.
# it adds parameters with a prefix of 'parent_lookup_' to self.kwargs

# Here we define newsItem and /newsItem/ID/ratings
router = ExtendedDefaultRouter(trailing_slash=False)
router.register(r"submissions", SubmissionViewSet)
router.register(r"moderatedsubmissions", ModeratedSubmissionViewSet)
router.register(r"users", UserViewSet)
# router.register(r'groups', GroupViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
]


urlpatterns = [
    path("admin/", admin.site.urls),
]

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns += [
    path("", include(router.urls)),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
]

schema_view = get_schema_view(  # pylint: disable=invalid-name
    openapi.Info(
        title="Dognews Server API",
        default_version="v1",
        description="API For the dog news server application",
        terms_of_service="",
        contact=openapi.Contact(email="contact-openapi@gatillos.com"),
        license=openapi.License(name="https://creativecommons.org/licenses/by-nd/3.0/"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns += [
    url(
        r"^swagger(?P<format>\.json|\.yaml)$",
        schema_view.without_ui(cache_timeout=0),
        name="schema-json",
    ),
    url(
        r"^swagger/$",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    url(
        r"^redoc/$", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"
    ),
]

# For Token based authentication - this endpoint allows a user to request a token by
# sending user/password auth/login is chosen by us
#
# note: we can also do
#   ./manage.py drf_create_token <username>       (creates or retrieves)
#   ./manage.py drf_create_token -r <username>      (regenerates)
urlpatterns += [url(r"^auth/login", authviews.obtain_auth_token)]

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
