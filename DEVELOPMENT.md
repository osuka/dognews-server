# Development notes

Some notes on this project. Most of this comes from following the [official tutorial](https://docs.djangoproject.com/en/2.2/intro/tutorial01/)

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
python manage.py createsuperuser --email admin@xxxxxxx.com --username adminz
```

Changing the default name just because.  Ff3MLujytDMukXHSSU8r

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

