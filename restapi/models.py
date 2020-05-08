from django.db import models
from django.contrib.auth.models import User
import django.utils
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token

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

# We are using Token authentication - the Tokens are created on user
# creation, by listening to the post+save event on the user model
# https://www.django-rest-framework.org/api-guide/authentication/#tokenauthentication
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)


class NewsItem(models.Model):
    """
    Represents a submitted news item and the different stages it goes through,
    from a mere url with a title and submitter to a summarised and analised
    entity that has been reviewed and rated by users
    """

    # mandatory fields
    target_url = models.CharField(max_length=250, unique=True)
    date = models.DateTimeField(
        default=django.utils.timezone.now
    )  # date can be modified but defaults to now
    title = models.CharField(max_length=250)
    source = models.CharField(max_length=250)
    submitter = models.CharField(max_length=25)

    fetch_date = models.DateTimeField(default=django.utils.timezone.now)

    # stubs for properties that come from OpenGraph
    image = models.CharField(max_length=250, default=None, blank=True, null=True)
    type = models.CharField(max_length=50, default=None, blank=True, null=True)

    # calculated properties
    body = models.CharField(max_length=512, default=None, blank=True, null=True)

    cached_page = models.CharField(max_length=120, default=None, blank=True, null=True)
    thumbnail = models.CharField(max_length=120, default=None, blank=True, null=True)

    summary = models.CharField(max_length=4096, default=None, blank=True, null=True)
    sentiment = models.CharField(max_length=20, default=None, blank=True, null=True)

    PUBLISHED = "P"
    APPROVED = "A"
    DISCARDED = "D"
    PENDING = ""
    PUBLICATION_STATES = [
        (PUBLISHED, "Published"),
        (APPROVED, "Approved"),
        (DISCARDED, "Discarded"),
        (PENDING, "-"),
    ]
    publication_state = models.CharField(
        max_length=1,
        choices=PUBLICATION_STATES,
        default=PENDING,
        blank=True,
        verbose_name="PubStatus",
    )


class Rating(models.Model):
    """
    Ratings given to an item from a user
    """

    # has a many to one link to a NewsItem
    # this appears as a 'ratings' field in NewsItem instances that is called 'ratings'
    newsItem = models.ForeignKey(
        NewsItem,
        blank=True,
        null=True,
        related_name="ratings",
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(User, null=False, on_delete=models.DO_NOTHING)
    RATING_VALUES = [
        (-1, "Bad"),
        (0, "Neutral"),
        (1, "Good"),
        (2, "Awesome"),
    ]
    rating = models.IntegerField(default=0, choices=RATING_VALUES)
    date = models.DateTimeField(auto_now=True)  # date changes on every save

    def __str__(self):
        return f"Rating({self.user},{self.rating})"
