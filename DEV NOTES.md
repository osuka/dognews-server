# Development notes

> Some notes I took while creating this project - nothing fancy but may help troubleshooting
> Most of this comes from following the [official tutorial](https://docs.djangoproject.com/en/2.2/intro/tutorial01/)

## Initial project creation

> Check [virtualenv](https://virtualenv.pypa.io/en/stable/) for more. Check [django](https://docs.djangoproject.com/en/3.0/) for more.

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

### Enable pagination on responses

We can easily configure the rest framework to return paginated results, in settings.py:

```python
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10
}
```

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

## Populate initial data

Create an empty migration:

```
DJANGO_SETTINGS_MODULE=xxxx python manage.py makemigrations restapi --empty
```

This will generate a file in `restapi/migrations/00XX_auto_YYYYDDMM_HHMM.py`.

It will contain a reference to the predecesor (last migration) automatically added.

Django contains some magic that allows you to use the models as they were in a point in time

```python
def create_admin_group(apps, schema_editor):
    # very important to not import directly the model
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    admin_group, _ = Group.objects.get_or_create(name=f"admin")
    admin_group.permissions.add(
        *Permission.objects.filter(codename="view_newsitem"),
        *Permission.objects.filter(codename="add_newsitem"),
        *Permission.objects.filter(codename="change_newsitem"),
        *Permission.objects.filter(codename="delete_newsitem"),
        *Permission.objects.filter(codename="view_rating"),
        *Permission.objects.filter(codename="add_rating"),
        *Permission.objects.filter(codename="change_rating"),
        *Permission.objects.filter(codename="delete_rating"),
    )
    admin_group.save()
```

Then we just have to add the operation to the list of things to do on this migration:

```
operations = [
        migrations.RunPython(create_admin_group),
    ]
```

You can execute them by running `./manage.py migrate`

## Per object permissions

### Trying djang-guardian

The default model permissions are good for quick admin pages, as they determine which staff users have access to what in a broad sense.
* Example: users in the group 'admins' can see and edit all models
* Example: users in the group 'new_moderators' can see and edit all articles in the News model, but nothing else etc

For external or system users we may want some more specific permissions. We can do this by overriding the has_permission method but there are also frameworks that fulfill this.
* Example: a user can change their own rating, but not any other's

With django-guardian: add it to `requirements.txt` and add 'guardian' to `INSTALLED_APPS` `in settings.py`.

Add `'guardian.backends.ObjectPermissionBackend',` to the `AUTHENTICATION_BACKENDS` (at the end), or add the whole variable if missing:

```python
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend', # default
    'guardian.backends.ObjectPermissionBackend',
)
```

This creates the tables 'guardian_groupobjectpermission' and 'guardian_userobjectpermission'.

Run `manage.py migrate`.

From then on you can add permissions to specific objects, for instance now we can make sure that existing users can
only modify their own ratings by allowing the 'change' permission only to the own user:

```python
from guardian.models import UserObjectPermission
for newsItem in NewsItem.objects.all():
    for rating in newsItem.ratings.all():
        UserObjectPermission.objects.assign_perm('change_rating', rating.user, obj=rating) # would not be allowed delete
```

We will need code to add this logic on creation. **For Admin pages** we can use the PermissionRequireMixin:

```python
class NewsItemView(PermissionRequiredMixin, ModelView)
    def form_valid(self, *args, **kwargs):
        resp = super().form_valid(*args, **kwargs)
        assign_perm('view_article', self.request.user, self.object)
        assign_perm('change_article', self.request.user, self.object)
        assign_perm('delete_article', self.request.user, self.object)
        return resp
```

This doesn't seem to be the best match for this particular app mostly because of the database approach, but it does allow a model I may like so I'll leave this as a reference here.

### Trying django-rules

This is [another per-model permission framework](https://github.com/dfunckt/django-rules) that offers integration with django-rest-framework.

Installation: add 'django-rules' to requirements.txt, 'rules' to INSTALLED_APPS, set the auth backends:

```python
AUTHENTICATION_BACKENDS = (
    'rules.permissions.ObjectPermissionBackend',
    'django.contrib.auth.backends.ModelBackend',
)
```

This framework is based on the concept of 'predicates', instead of database rules these are functions that determine if a permission is given or not.
Any function can be a predicate.

There's some useful predefined predicates:

* is_authenticated(user)
* is_superuser(user)
* is_staff(user), staff users
* is_active(user)
* is_group_member(*groups)  (must pertain to all of those groups)

```python
@rules.predicate
def belongs_to_user(user, rating):
    return rating.user == user

# option 1: there is a 'bag' of rules we can use if we add them in models or views:
rules.add_rule('belongs_to_user', belongs_to_user)

# option 2: we can instead define a 'permission' which is a rule associated to a model
rules.add_perm('rating.change_rating', belongs_to_user | is_staff)

# option 3: (needs !) we can also declare them as part of the models themselves
from django.db import models
from rules.contrib.models import RulesModelBase, RulesModelMixin
class NewsItem(RulesModelMixin, models.Model, metaclass=RulesModelBAse):
    class Meta:
        rules_permissions = {
            'add': rules.is_staff
            'change': belongs_to_user | rules.is_staff,
        }

# option 4: (needs 2) we can add them to views
from rules.contrib.views import PermissionRequiredMixin
class NewsItemUpdate(PermissionRequiredMixin, UpdateView):
    model = NewsItem
    permission_required = 'rating.change_rating'

```

> Predicates can be combined with &, |, ^ (P1 ^ P2 = true if only one of them is True), ~

### Going back to basics

Overall it all seems a bit too magic and not part of django or django-rest-framework so instead of that I'm going to basic and do it implementing the has_permission methods
as in [the official django-rest-framework documentation](https://www.django-rest-framework.org/api-guide/permissions/)

For the example of newsItem:

```python

# an example of a non-per object permission
class IsAuthenticated(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

# an example of a per-object permission
class IsOwnerOrStaff(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if view.action == 'update' or view.action == 'partial_update' or view.action == 'destroy':
            return obj.user == request.user or request.user.is_staff
        return True

class RatingViewSet(viewsets.ModelViewSet):
    serializer_class = RatingSerializer
    queryset = Rating.objects.all()
    permission_classes = (IsOwnerOrStaff,)
```

Note that above, to not split the viewset into the individual views (because it's nicer to have less code), I've added a check in the permission itself, so it does one thing or another depending on the action.

For extended cases it's probably better to just not use ViewSets and instead use the generic views directly, like:

```python
class UserView(generics.ListCreateAPIView):
    permission_classes = (...,)
    ...

class UserView(generics.UpdateAPIView):
    permission_classes = (...,)
    ...
```

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

## Helpful tools

```sh
./manage.py shell

./manage.py dbshell

./manage.py changepassword {username}
```

Then you can import models, list, create etc
