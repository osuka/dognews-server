# Development notes

<!-- TOC depthFrom:2 orderedList:true -->autoauto1. [Initial project creation](#initial-project-creation)auto2. [Adding REST Django framework](#adding-rest-django-framework)auto  1. [Create serializers for the auth objects](#create-serializers-for-the-auth-objects)auto  2. [Create some views for the auth objects](#create-some-views-for-the-auth-objects)auto  3. [Map views to urls](#map-views-to-urls)auto  4. [Enable pagination on responses](#enable-pagination-on-responses)auto3. [Browseable API](#browseable-api)auto4. [Creating new models](#creating-new-models)auto5. [Creating admin pages for our models](#creating-admin-pages-for-our-models)auto6. [Auto Generating documentation](#auto-generating-documentation)auto7. [Creating per-environment configuration](#creating-per-environment-configuration)auto8. [Helpful tools](#helpful-tools)autoauto<!-- /TOC -->

> Some notes I took while creating this project - nothing fancy but may help troubleshooting
> Most of this comes from following the [official tutorial](https://docs.djangoproject.com/en/2.2/intro/tutorial01/)

<a id="markdown-initial-project-creation" name="initial-project-creation"></a>
## Initial project creation

> Check [virtualenv](https://virtualenv.pypa.io/en/stable/) for more
> Check [django](https://docs.djangoproject.com/en/3.0/)

```sh
virtualenv -p python3.8 venv
source venv/bin/activate
echo 'Django>=3' >>requirements.txt
pip install -r requirements.txt
django-admin startproject dognews
```

Now we have the following structure:

```text
├── venv
├── requirements.txt
└── dognews
    ├── dognews
    │   ├── __init__.py
    │   ├── settings.py  <--- DB configuration, auth, i18n, static
    │   ├── urls.py    <--- routes, 'admin/' pointing to default Admin UI
    │   └── wsgi.py   <-- for gunicorn et al
    └── manage.py   <-- tool we will use to further interact with django admin
```

> Note that the top level 'dognews' name isn't used, and it's all redundant so I moved dognews/dognews and manage.py one folder up

```text
├── dognews
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── manage.py
├── requirements.txt
└── venv
```

Run it

```sh
source venv/bin/activate
./manage.py --help
./manage.py migrate         # init database
./manage.py runserver 8181  # test it
```

Going to [localhost:8181/admin](http://localhost:8181/admin) you can check it's running.

After the `migrate` command above, the db has some tables now:

```bash
> ./manage.py dbshell
sqlite> .databases
main: /(...)/dognews-server/db.sqlite3
sqlite> .tables
auth_group                  auth_user_user_permissions
auth_group_permissions      django_admin_log
auth_permission             django_content_type
auth_user                   django_migrations
auth_user_groups            django_session
```

Finally we need to create an initial _superuser_

```bash
python manage.py createsuperuser --email xxxx@xxxxxxx.xxx --username XXXXX
```

<a id="markdown-adding-rest-django-framework" name="adding-rest-django-framework"></a>
## Adding REST Django framework

> Check [Django Rest Framework](https://www.django-rest-framework.org/)

DRF helps build production ready APIs with minimal code and it integrates with existing django models and project structure.

```sh
echo 'djangorestframework>=3' >>requirements.txt
pip install -r requirements
```

Enable the rest framework itself by adding the string `'rest_framework'` to the `INSTALLED_APPS` array in [./dognews/settings.py](./dognews/settings.py).

A few quick concepts in Django Rest Framework:

* Serializer: representation of the model, similar to a POJO in java, or a json object
* View: the exposed actions (determins what urls are available and what is shown on each, for instance 'a list of all user')

<a id="markdown-create-serializers-for-the-auth-objects" name="create-serializers-for-the-auth-objects"></a>
### Create serializers for the auth objects

The auth module (check [django.contrib.auth on Django](https://docs.djangoproject.com/en/3.0/ref/contrib/auth/)) is standard in django and provides simple user/group/permission authentication and authorization.

```python
from django.contrib.auth.models import User, Group
from rest_framework import serializers

class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'groups']

class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ['url', 'name']
```

Add this to `restapi/serializers.py`

<a id="markdown-create-some-views-for-the-auth-objects" name="create-some-views-for-the-auth-objects"></a>
### Create some views for the auth objects

We will not be actually publishing user and group lists via REST these for this application, but they are an easy way to get to grips with the concepts:

```python
from django.contrib.auth.models import User, Group
from rest_framework import viewsets
from tutorial.quickstart.serializers import UserSerializer, GroupSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer

class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
```

We add this to the existing `restapi/views.py`

> Note! There is a 'trick' here in that the 'ViewSet' is actually creating a lot of Views for the common behaviour associated to a model. In this case we give it the starting point, a query to the User model and that is enough for it to figure out views to list / add / delete and patch (update) entries. For some corner cases we may need to add individual views, or override those. It's exposing:
> * OPTIONS: to get a list of available actions for a URL and content types allowed
> * GET, PUT, DELETE according to the model and relations

<a id="markdown-map-views-to-urls" name="map-views-to-urls"></a>
### Map views to urls

Finally we just need to publish the views we have created using the rest framework version of a 'router':

```python
from django.urls import include, path
from rest_framework import routers
from tutorial.quickstart import views

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'groups', views.GroupViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]
```

With this we are publishing under `/users`, `/groups` and ca do things like `GET /users/0/groups`.

About the `api-auth/` URLs there, they are suggested by the DRF tutorial:
> Finally, we're including default login and logout views for use with the browsable API. That's optional, but useful if your API requires authentication and you want to use the browsable API.

<a id="markdown-enable-pagination-on-responses" name="enable-pagination-on-responses"></a>
### Enable pagination on responses

We can easily configure the rest framework to return paginated results, in settings.py:

```python
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10
}
```

<a id="markdown-browseable-api" name="browseable-api"></a>
## Browseable API

Django Rest Framework exposes a UI that can be used to browse the API with a nice HTML page that lets you click around, POST, GET, PUT, DELETE.

Example: Going to [localhost:8181](http://localhost:8181) shows this _Browseable API_ list of available URLs:

```text
HTTP 200 OK
Allow: GET, HEAD, OPTIONS
Content-Type: application/json
Vary: Accept
{
    "users": "http://localhost:8181/users/",
    "groups": "http://localhost:8181/groups/"
}
```

Click on the users and groups links to go to their pages.

You can verify / use an alternative editor through the Django Admin console, which is unrelated to the django rest framework and  lives under `/admin` [localhost:8181/admin](http://localhost:8181/admin).

> NOTE: password is not in the forms displayed by REST for the users, nor is it in the Admin console UI directly. Password change is done through `http://localhost:8181/admin/password_change` in the admin console, that has the typical 'previous password' requirement.

<a id="markdown-creating-new-models" name="creating-new-models"></a>
## Creating new models

This project is going to be very simple so we will likely only have one 'app' (it's a modular unit for django, a subset of functionality).

```sh
django-admin startapp restapi
```

This is the structure now:

```text
├── db.sqlite3       <-- empty initial database
├── dognews
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── manage.py
├── requirements.txt
├── restapi
│   ├── admin.py
│   ├── apps.py
│   ├── __init__.py
│   ├── migrations
│   │   └── __init__.py
│   ├── models.py
│   ├── tests.py
│   └── views.py
└── venv
```

Created some basic stubs of the models that you ca see here [./restapi/models.py](./restapi/models.py)

A model is just the definition of fields, relations and restrictions (validations) for an entity.

> Check [Django's guide on modules](https://docs.djangoproject.com/en/3.0/topics/db/models/)

Some notes:

* blank=True defines a field as not required
* for dates, we set default=django.admin.timezone.now - note that we pass the function, not a value - this sets the correct now() field on save, using datetime.now() would just store the one at launch time
* need to add to INSTALLED_APPS 'restapi' so it loads it
* the n to m relation between news item and its ratings is defined in ratings with a FK field: `newsItem = models.ForeignKey(NewsItem, on_delete=models.CASCADE)`
* for embedded serialization (ie newsitem object includes a list of rating objects), simply generate a serializer for ratings and add it to the newsitem serializer as `ratings = RatingSerializer(many=True, required=False)`
* to represent externally in a json API where you can update a rating directly with a patch, I'm using the python module `rest_framework_nested`, an extension to django rest framework: creating a new nested router inside urls.py for it and extending the serializer to work nicely with it

Every time we modify the models, a migration needs to be created. Django does this magically with:

```bash
> ./manage.py makemigrations restapi
Migrations for 'restapi':
  restapi/migrations/0001_initial.py
    - Create model NewsItem
    - Create model NewsItemRating
```

<a id="markdown-creating-admin-pages-for-our-models" name="creating-admin-pages-for-our-models"></a>
## Creating admin pages for our models

Add to [./restapi/admin.py](./restapi/admin.py) what we want shown on the /admin pages:

```python
class NewsItemRatingInline(admin.StackedInline):
    model = NewsItemRating
    min_num = 0
    extra = 0  # determines number of empty elements for new objects

@admin.register(NewsItem)
class NewsItemAdmin(admin.ModelAdmin):
    inlines = [
        NewsItemRatingInline
    ]
```

> Note: without extra = 0 it creates 3 empty objects in the form (this is in InlineModelAdmin, where it declares extra = 3 god knows why)

<a id="markdown-auto-generating-documentation" name="auto-generating-documentation"></a>
## Auto Generating documentation

There are a few ways to go about this. One thing we can do is manually generate an OpenAPI Schema representation. This is a yaml document expressing all the exposed methods that we have

```sh
python manage.py generateschema > openapi-schema.yml
```

> A lot can be tweaked here, check [docs](https://www.django-rest-framework.org/api-guide/schemas/)

There's tools that can consume that file and output various types of documentation pages.

Since I'm using django rest framework I'll be using [drf-yasg](https://github.com/axnsan12/drf-yasg) that integrates nicely with it. With a couple of changes the documentation will appear 'magically':

* Load drf_yasg as an application in settings.py
* Create a schema_view in urls.py using its get_schema_view function
* Expose the patterns we want for swagger json/yaml, swagger UI and/or redoc (alternative view)

Exposed URLs are:

* /swagger.json
* /swagger.yaml
* /swagger/
* /redoc/

<a id="markdown-creating-per-environment-configuration" name="creating-per-environment-configuration"></a>
## Creating per-environment configuration

I have currently three needs: local, dreamhost and test

Created:

* requirements.txt (common)
* requirements.dreamhost.txt
* requirements.test.txt
* module dognews.settings
  * base.py (common)
  * dreamhost.py (imports base, extends)
  * local.py
  * test.py

Launch with settings:

```sh
export DJANGO_SETTINGS_MODULE=dognews.settings.local
python manage.py runserver
```

<a id="markdown-helpful-tools" name="helpful-tools"></a>
## Helpful tools

```sh
./manage.py shell

./manage.py dbshell

./manage.py changepassword {username}
```

Then you can import models, list, create etc