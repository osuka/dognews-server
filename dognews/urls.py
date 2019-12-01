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
from rest_framework import routers
from rest_framework_nested.routers import NestedDefaultRouter
from restapi import views

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'groups', views.GroupViewSet)
router.register(r'newsItem', views.NewsItemViewSet)

print(router.urls)

urlpatterns = [
    path('admin/', admin.site.urls),
]

# from https://github.com/alanjds/drf-nested-routers
newsitem_router = NestedDefaultRouter(router, r'newsItem', lookup='newsItem')
newsitem_router.register(r'ratings', views.RatingViewSet, base_name='newsItem-ratings')
# 'base_name' is optional. Needed only if the same viewset is registered more than once
# Official DRF docs on this option: http://www.django-rest-framework.org/api-guide/routers/

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns += [
    path('', include(router.urls)),
    path('', include(newsitem_router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]
