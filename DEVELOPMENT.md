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

python manage.py startapp polls