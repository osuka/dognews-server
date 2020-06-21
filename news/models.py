from django.db import models
from django.contrib.auth.models import User
import django.utils
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
import tldextract

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


class Submission(models.Model):
    """
    Represents a submitted news item. This is produced by an authorized user
    (even if it's a bot). Items are processed once to fetch the information
    from the url and then are discarded or moved to the moderation queue
    """

    class Statuses(models.TextChoices):
        NEW = "new", "Processing"
        ACCEPTED = "accepted", "Ready for review"
        REJECTED_COULD_NOT_FETCH = "rej_fetch", "Rejected: Could not fetch"
        REJECTED_BLACKLISTED_DOMAIN = "rej_list", "Rejected: Blacklisted domain"
        REJECTED_MODERATOR = "rej_mod", "Rejected: Moderator action"

    target_url = models.URLField(unique=True)
    owner = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        editable=False,
        related_name="submissions",
    )
    title = models.CharField(max_length=120, blank=True, default="")
    description = models.CharField(max_length=250, blank=True, default="")
    status = models.CharField(
        max_length=10, choices=Statuses.choices, default=Statuses.NEW, editable=False
    )
    date_created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)

    fetched_page = models.TextField(
        max_length=60 * 1024, default=None, blank=True, null=True, editable=False
    )
    fetched_date = models.DateTimeField(null=True, default=None, editable=False)

    @property
    def domain(self):
        if self.target_url:
            try:
                extracted = tldextract.extract(self.target_url)
                domain = f"{extracted.domain}.{extracted.suffix}"
                return domain
            except:
                pass

    def move_to_moderation(self):
        self.status = self.Statuses.ACCEPTED
        moderated_submission = ModeratedSubmission.objects.create(submission=self,)
        moderated_submission.save()
        self.save()

    def __str__(self):
        return f"{self.id} ({self.domain[:20]}...)"


class ModeratedSubmission(models.Model):
    """
    Stores posted items that have been retrieved while bots and humans process them.
    First bots iterate over them updating fields and finally setting it to Ready for review,
    then users (collaborators) can view them, vote for them and moderators can
    publish them
    """

    class Statuses(models.TextChoices):
        NEW = "new", "Processing"
        READY = "ready", "Ready for review"
        ACCEPTED = "accepted", "Accepted"
        REJECTED_COULD_NOT_FETCH = "rej_spam", "Rejected: It's spam"
        REJECTED_BLACKLISTED_DOMAIN = "rej_dupe", "Rejected: Duplicate"
        REJECTED_DOWNVOTED = "rej_votes", "Rejected: Users downvoted"
        REJECTED_OTHER = "rejected", "Rejected: Other"

    submission = models.OneToOneField(
        to=Submission, on_delete=models.SET_NULL, null=True
    )
    target_url = models.URLField(unique=True, blank=True, null=True, default=None)
    title = models.CharField(max_length=120, blank=True, null=True, default=None)
    description = models.CharField(max_length=250, blank=True, null=True, default=None)
    thumbnail = models.CharField(
        max_length=250, null=True, blank=True, default=None, editable=False
    )
    status = models.CharField(
        max_length=10, choices=Statuses.choices, default=Statuses.NEW
    )
    last_modified_by = models.ForeignKey(
        to=User,
        on_delete=models.SET_NULL,
        null=True,
        editable=False,
        related_name="moderated_submissions",
    )
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    date_created = models.DateTimeField(auto_now_add=True, editable=False)

    bot_title = models.CharField(
        max_length=120, null=True, blank=True, default=None, editable=False
    )
    bot_description = models.CharField(
        max_length=250, null=True, blank=True, default=None, editable=False
    )
    bot_summary = models.TextField(null=True, blank=True, default=None, editable=False)
    bot_sentiment = models.TextField(
        null=True, blank=True, default=None, editable=False
    )
    bot_thumbnail = models.CharField(
        max_length=250, null=True, blank=True, default=None, editable=False
    )

    def save(self, *args, **kwargs):
        # auto populate from the chose submission
        if self.submission and (
            not self.description or not self.title or not self.target_url
        ):
            self.description = (
                self.submission.description
                if not self.description
                else self.description
            )
            self.title = self.submission.title if not self.title else self.title
            self.target_url = (
                self.submission.target_url if not self.target_url else self.target_url
            )
        super().save(*args, **kwargs)

    # + ratings: is a one-to-many relation, see Rating
    def __str__(self):
        return f"{self.id} ({self.target_url[:20]})"


class Vote(models.Model):
    """ Vote/rating provided by a user for a submitted item """

    class Values(models.IntegerChoices):
        UP = 1, "👍"
        DOWN = -1, "👎"
        FLAG = -100, "💩"

    moderated_submission = models.ForeignKey(
        to=ModeratedSubmission,
        on_delete=models.SET_NULL,
        null=True,
        editable=False,
        related_name="votes",
    )
    owner = models.ForeignKey(
        to=User,
        on_delete=models.SET_NULL,
        null=True,
        editable=False,
        related_name="votes",
    )
    value = models.SmallIntegerField(choices=Values.choices, default=Values.UP)

    last_updated = models.DateTimeField(auto_now=True, editable=False)
    date_created = models.DateTimeField(auto_now_add=True, editable=False)

    def __str__(self):
        return f"{self.id} ({self.owner},{self.moderated_submission},{self.value})"

    class Meta:
        unique_together = [("owner", "moderated_submission")]


class Article(models.Model):
    """
    Articles that have been accepted for publication. This is a small table with only the final
    version of articles after review and moderation.
    """

    target_url = models.URLField(unique=True)
    title = models.CharField(max_length=120)
    description = models.CharField(max_length=250)
    thumbnail = models.CharField(
        max_length=250, null=True, blank=True, default=None, editable=False
    )
    submitter = models.ForeignKey(
        to=User,
        on_delete=models.SET_NULL,
        null=True,
        editable=False,
        related_name="articles",
    )
    moderated_submission = models.OneToOneField(
        to=ModeratedSubmission, on_delete=models.SET_NULL, null=True, editable=False
    )
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    date_created = models.DateTimeField(auto_now_add=True, editable=False)

    def __str__(self):
        return f"{self.id} ({self.target_url[:20]},{self.date_created})"

