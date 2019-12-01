# Development notes

> Some notes I took while creating this project - nothing fancy but may help troubleshooting
> Most of this comes from following the [official tutorial](https://docs.djangoproject.com/en/2.2/intro/tutorial01/)

## Initial project creation

1. Created a virtualenv -p python3 venv
2. Activated virtualenv (source venv/bin/activate)
3. Created requirements.txt with just 'Django>=2' in it (could have used 2.2)
4. pip install -r requirements.txt
5. Check it's there:  python -m django --version
6. Scaffold a project: django-admin startproject dognews (note the name has to be valid for a python module, no dashes)

Now we have the following structure:

```text
├── DEVELOPMENT.md
├── venv
├── requirements.txt
└── dognews
    ├── dognews
    │   ├── __init__.py
    │   ├── settings.py  <--- DB configuration, auth, i18n, static
    │   ├── urls.py    <--- views, initially only  path('admin/', django.contrib.admin.site.urls), the default Admin App
    │   └── wsgi.py   <-- declares an 'application' module that wsgi expects
    └── manage.py   <-- wrapper around django.core.management.execute_from_command_line
```

Note that the top level 'dognews' name isn't used, and it's all redundant so I move dognews/dognews and manage.py one folder
up: `mv dognews _dognews ; mv _dognews/* .` so now the structure is:

```text
├── DEVELOPMENT.md
├── dognews
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── manage.py
├── requirements.txt
└── venv

We can run `python manage.py` and see the different options. We can test it with:

```bash
python manage.py runserver 8181
```

Going to localhost:8181 will show:

> The install worked successfully! Congratulations!
> You are seeing this page because DEBUG=True is in your settings file and you have not configured any URLs.

From the docs:

> Projects vs. apps: What’s the difference between a project and an app? An app is a Web application that does something – e.g., a Weblog system, a database of public records or a simple poll app. A project is a collection of configuration and apps for a particular website. A project can contain multiple apps. An app can be in multiple projects.

Now we can create our app, that we will call restapi

```bash
django-admin startapp restapi
```

This is the structure now:

```text
├── db.sqlite3       <-- empty initial database
├── DEVELOPMENT.md
├── dognews
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── manage.py
├── requirements.txt
├── restapi
│   ├── admin.py         <-- placeholder for links to models
│   ├── apps.py        <-- placeholder for app config (class RestapiConfig(AppConfig))
│   ├── __init__.py
│   ├── migrations         <--- empty
│   │   └── __init__.py
│   ├── models.py      <-- placeholder for models
│   ├── tests.py     <--- placeholder for tests
│   └── views.py    <--- placeholder for views
└── venv
```

All placeholders are just empty

## Adding REST Django framework

This section follows the [official tutorial](https://www.django-rest-framework.org/tutorial/quickstart/)

Add `djangorestframework>=3` to requirements.txt (the 3 comes from searching with pip and seeing the latest version)

Now that we have the project we create this first app, instead of a web site this will be the REST server

Note that django seems to recommend having restapi inside dognews, so it inherits the namespace. To do so, they
call startapp from inside the `dognews` folder. This is to avoid name classes. I _guess_ it will be ok.

Sync the database:

```bash
-> % python manage.py migrate
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, sessions
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  Applying admin.0001_initial... OK
  Applying admin.0002_logentry_remove_auto_add... OK
  Applying admin.0003_logentry_add_action_flag_choices... OK
  Applying contenttypes.0002_remove_content_type_name... OK
  Applying auth.0002_alter_permission_name_max_length... OK
  Applying auth.0003_alter_user_email_max_length... OK
  Applying auth.0004_alter_user_username_opts... OK
  Applying auth.0005_alter_user_last_login_null... OK
  Applying auth.0006_require_contenttypes_0002... OK
  Applying auth.0007_alter_validators_add_error_messages... OK
  Applying auth.0008_alter_user_username_max_length... OK
  Applying auth.0009_alter_user_last_name_max_length... OK
  Applying auth.0010_alter_group_name_max_length... OK
  Applying auth.0011_update_proxy_permissions... OK
  Applying sessions.0001_initial... OK
```

Taking a look into the database:

```bash
-> % sqlite3 db.sqlite3
sqlite> .databases
main: /home/osuka/Documents/non-shared-code/dognews-server/db.sqlite3
sqlite> .tables
auth_group                  auth_user_user_permissions
auth_group_permissions      django_admin_log
auth_permission             django_content_type
auth_user                   django_migrations
auth_user_groups            django_session
sqlite>
```

Most tables are empty except django_migrations which logs what has already happened, and auth_permission, django_content_type that have 'factory' values.

### Create the initial superuser

```bash
python manage.py createsuperuser --email admin@xxxxxxx.com --username XXXXX
```

Changing the default name just because.

### Create default serializers

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

This goes into the restapi folder in a file called `serializers.py`

### Create default views

```python
from django.contrib.auth.models import User, Group
from rest_framework import viewsets
from tutorial.quickstart.serializers import UserSerializer, GroupSerializer
class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
```

We add this to the existing views.py

The tutorial says:
> Rather than write multiple views we're grouping together all the common behavior into classes called ViewSets, We can easily break these down into individual views if we need to, but using viewsets keeps the view logic nicely organized as well as being very concise.

### Create default urls

```python
from django.urls import include, path
from rest_framework import routers
from tutorial.quickstart import views

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'groups', views.GroupViewSet)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]
```

This belongs to the project, so it goes in dognews/urls.py. I keep the original 'admin' url
that existed them when adding this.

The tutorial says:
> Because we're using viewsets instead of views, we can automatically generate the URL conf for our API, by simply registering the viewsets with a router class.
> Finally, we're including default login and logout views for use with the browsable API. That's optional, but useful if your API requires authentication and you want to use the browsable API.

### Enable pagination

In settings.py:

```python
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10
}
```

We also enable the rest framework itself by adding `rest_framework` to `INSTALLED_APPS` in settings.py, and we can `python manage.py runserver 8181` again.

Going to localhost:8181 already shows a UI that exposes a root view that functions as a kind of wrapper. It displays what you would get from curl, but also makes the links clickable. So going to
http://localhost:8181 on the browser displays this:

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

And you can click on the users and groups links to go to their pages.

The users one will display the adminz user we created before.

It lets you POST to create a new one (provides a form), or you can click on the 'url' property that each user has to edit.

Going to http://localhost:8181/admin opens the Django Admin console (aside from REST framework, it's one of the apps installed in settings.py)
It shows a list of groups and users.

### Note: password change

NOTE: password is not in the forms displayed by REST for the users, nor is it in the Admin console UI.

The password is stored in a table:

```sql
sqlite> select * from auth_user;
1|pbkdf2_sha256$150000$FPyJ6CLXXXXXXXXXXXXXXXXXXXXXXXXXXb36ioJmuQVc=||1|adminz||admin@xxxxxx.com|1|1|2019-11-01 16:40:14.395038|
```

Password change is done through `http://localhost:8181/admin/password_change` in the admin console, that has the typical 'type previous' etc.

## Run development server

```
python manage.py runserver
```

## Creating the models

We have already defined models in the react API and news-extractor applications, now we just migrate them to django-style. I continue the [rest framework tutorials](https://www.django-rest-framework.org/tutorial/1-serialization/)

An excerpt from sample model from the tutorial:

```python
class Snippet(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=100, blank=True, default='')
    code = models.TextField()
    linenos = models.BooleanField(default=False)
    ...
    class Meta:
        ordering = ['created']
```

Some notes:

* blank=True defines a field as not required
* for dates, we set default=django.admin.timezone.now - this sets the correct now() field on save, using datetime.now() would just store the one at launch time
* need to add to INSTALLED_APPS 'restapi' so it loads our models
* the n to m relation between news item and its ratings is defined in ratings with a FK field: `newsItem = models.ForeignKey(NewsItem, on_delete=models.CASCADE)`
* for embedded serialization (ie newsitem object includes a list of rating objects), simply generate a serializer for ratings and add it to the newsitem serializer as `ratings = RatingSerializer(many=True, required=False)`
* to represent externally in a json API where you can update a rating directly with a patch, I'm using the python module `rest_framework_nested`, an extension to django rest framework: creating a new nested router inside urls.py for it and extending the serializer to work nicely with it

To generate the tables:

```bash
-> % python manage.py makemigrations restapi
Migrations for 'restapi':
  restapi/migrations/0001_initial.py
    - Create model NewsItem
    - Create model NewsItemRating
```

## Creating admin pages

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

* without extra = 0 it creates 3 empty objects in the form (this is in InlineModelAdmin, where it declares extra = 3 god knows why)


## Generating documentation

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

## Run a shell inside django

```sh
python manage.py shell
```

Then you can import models, list, create etc