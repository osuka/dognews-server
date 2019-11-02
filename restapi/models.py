from django.db import models
from django.contrib.auth.models import User
import django.utils


class NewsItem(models.Model):
    # note: blank=True --> field is not required in forms

    # mandatory fields
    url = models.CharField(max_length=250, primary_key=True)
    date = models.DateTimeField(default=django.utils.timezone.now)
    title = models.CharField(max_length=250)
    source = models.CharField(max_length=80)
    submitter = models.CharField(max_length=25)
    # ratings = models.ManyToManyField('restapi.NewsItemRating')

    fetch_date = models.DateTimeField(default=django.utils.timezone.now)

    # stubs for properties that come from OpenGraph
    image = models.CharField(max_length=80, default=None, blank=True)
    type = models.CharField(max_length=50, default=None, blank=True)

    # calculated properties
    body = models.CharField(max_length=512, default=None, blank=True)

    cached_page = models.CharField(max_length=80, default=None, blank=True)
    thumbnail = models.CharField(max_length=80, default=None, blank=True)

    summary = models.CharField(max_length=4096, default=None, blank=True)
    sentiment = models.CharField(max_length=20, default=None, blank=True)


class NewsItemRating(models.Model):
    newsItem = models.ForeignKey(NewsItem, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    rating = models.IntegerField(default=0)
    date = models.DateTimeField(default=django.utils.timezone.now)

    def __str__(self):
        return f'Rating({self.user},{self.rating})'
