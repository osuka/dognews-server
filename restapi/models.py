from django.db import models
from django.contrib.auth.models import User
import django.utils

# django permissions note:
#
# Django by default creates, for every model, permissions like
# '<appname>.delete_<modelname>'
# '<appname>.change_<modelname>'
# '<appname>.create_<modelname>'
# '<appname>.view_<modelname>'
#
# But it does not enforce by default any restriction on viewing
# I have extended this by creation a new permission (in permissions.py):
#         'GET': ['%(app_label)s.view_%(model_name)s'],

# django null vs blank note:
#
# blank=True --> field is not required in forms, but still needs to be
#               provided as empty string if no default value is provided
# null=True --> field is not required in forms and can be stored as
#               null (None when read)

class NewsItem(models.Model):
    '''
    Represents a submitted news item and the different stages it goes through,
    from a mere url with a title and submitter to a summarised and analised
    entity that has been reviewed and rated by users
    '''


    # mandatory fields
    target_url = models.CharField(max_length=250, unique=True)
    date = models.DateTimeField(default=django.utils.timezone.now)
    title = models.CharField(max_length=250)
    source = models.CharField(max_length=80)
    submitter = models.CharField(max_length=25)
    # ratings = models.ManyToManyField('Rating', related_name='ratings', default=None, null=True)

    fetch_date = models.DateTimeField(default=django.utils.timezone.now)

    # stubs for properties that come from OpenGraph
    image = models.CharField(max_length=80, default=None, blank=True, null=True)
    type = models.CharField(max_length=50, default=None, blank=True, null=True)

    # calculated properties
    body = models.CharField(max_length=512, default=None, blank=True, null=True)

    cached_page = models.CharField(max_length=80, default=None, blank=True, null=True)
    thumbnail = models.CharField(max_length=80, default=None, blank=True, null=True)

    summary = models.CharField(max_length=4096, default=None, blank=True, null=True)
    sentiment = models.CharField(max_length=20, default=None, blank=True, null=True)


class Rating(models.Model):
    '''
    Ratings given to an item from a user
    '''
    newsItem = models.ForeignKey(NewsItem, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    rating = models.IntegerField(default=0)
    date = models.DateTimeField(default=django.utils.timezone.now)

    def __str__(self):
        return f'Rating({self.user},{self.rating})'
