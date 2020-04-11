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
from restapi import views


router = ExtendedDefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'groups', views.GroupViewSet)
router.register(r'newsItem', views.NewsItemViewSet).register(
    r'ratings', views.NewsItemRatingViewSet, basename='newsItem-ratings',
    parents_query_lookups=['newsItem_id'],
)
# the parent query lookups are part of the django extensions nested router

urlpatterns = [
    path('admin/', admin.site.urls),
]

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns += [
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls',
                              namespace='rest_framework')),
]

schema_view = get_schema_view(
    openapi.Info(
        title="Dognews Server API",
        default_version='v1',
        description="API For the dog news server application",
        terms_of_service="",
        contact=openapi.Contact(email="contact-openapi@gatillos.com"),
        license=openapi.License(name="https://creativecommons.org/licenses/by-nd/3.0/"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns += [
    url(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    url(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    url(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# For Token based authentication - this endpoint allows a user to request a token by sending user/password
# auth/login is chosen by us
#
# note: we can also do
#   ./manage.py drf_create_token <username>       (creates or retrieves)
#   ./manage.py drf_create_token -r <username>      (regenerates)
urlpatterns += [
    url(r'^auth/login', authviews.obtain_auth_token)
]
