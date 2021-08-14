"""
Models to handle new submissions and their lifecycle to becoming Articles
"""

import os
from datetime import datetime
from hashlib import sha1
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
import tldextract
from dogauth.models import User

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


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(
    sender, instance=None, created=False, **kwargs  # pylint: disable=unused-argument
):
    """
    Create an associated auth token for any created user.
    We are using Token authentication - the Tokens are created on user
    creation, by listening to the post+save event on the user model
    https://www.django-rest-framework.org/api-guide/authentication/#tokenauthentication
    """
    if created:
        Token.objects.create(user=instance)


class SubmissionStatuses(models.TextChoices):
    """Calculated lifecyle status of Submission entities"""

    PENDING = "pending", "Pending"
    ACCEPTED = "accepted", "A moderator accepted"
    REJECTED_MOD = "rej_mod", "Rejected: A moderator rejected it"
    REJECTED_FETCH = "rej_fetch", "Rejected: Could not be fetched"
    REJECTED_BANNED = "rej_banned", "Rejected: Domain is blocklisted"
    REJECTED_SENTIMENT = "rej_sentim", "Rejected: Sentiment analysis"


class ModerationStatuses(models.TextChoices):
    """Lifecycle status"""

    PENDING = "pending", "Pending"
    ACCEPTED = "accepted", "Moderator accepted"
    REJECTED = "rejected", "Moderator rejected"


class FetchStatuses(models.TextChoices):
    """Lifecycle status"""

    PENDING = "pending", "Pending"
    FETCHED = "fetched", "Fetched"
    REJECTED_ERROR = "rej_error", "Rejected: Could not fetch"
    REJECTED_BANNED = "rej_fetch", "Rejected: domain in blocklist"


class AnalysisStatuses(models.TextChoices):
    """Lifecycle status"""

    PENDING = "pending", "Pending"
    FAILED = "failed", "Failed"
    PASSED = "passed", "Passed"


# ----


class Submission(models.Model):
    """
    Represents a submitted news item. This is produced by an authorized user
    (even if it's a bot). Items are processed once to fetch the information
    from the url and then are discarded or moved to the moderation queue
    """

    # status is changed via signal triggering
    status = models.CharField(
        max_length=10,
        choices=SubmissionStatuses.choices,
        default=SubmissionStatuses.PENDING,
        editable=False,
    )
    target_url = models.URLField(unique=True)
    owner = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        editable=True,  # only via admin
        related_name="submissions",
    )
    last_modified_by = models.ForeignKey(
        to=User, on_delete=models.SET_NULL, null=True, editable=False
    )
    title = models.CharField(max_length=120, blank=True, default="")
    description = models.CharField(max_length=250, blank=True, default="")
    date = models.DateTimeField(null=True, editable=True)
    date_created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)

    @property
    def domain(self):
        """Extract the domain piece of the URL, for display and blacklisting"""
        if self.target_url:
            try:
                extracted = tldextract.extract(self.target_url)
                domain = f"{extracted.domain}.{extracted.suffix}"
                return domain
            except ValueError:
                pass

    def __str__(self):
        return f"{self.domain}({self.owner}:{self.id})"


def user_directory_path(instance, filename):
    """Defines where to save a file, using a hash of the filename"""
    # note that this path is relative to settings.MEDIA_ROOT
    key = sha1(filename.encode()).hexdigest()
    _, extension = os.path.splitext(filename)
    now = datetime.utcnow().strftime("%Y/%H/%M")
    username = (
        instance.submission.owner.id
        if instance.submission and instance.submission.owner
        else ""
    )
    return f"uploaded_images/{now}/{username}_{key}{extension}"


class Fetch(models.Model):
    """
    Stores data obtained after fetching the URL and parsing it
    """

    submission = models.OneToOneField(
        Submission, on_delete=models.CASCADE, primary_key=True
    )
    status = models.CharField(
        max_length=10,
        choices=FetchStatuses.choices,
        default=FetchStatuses.PENDING,
        editable=True,
    )
    owner = models.ForeignKey(
        to=User, on_delete=models.SET_NULL, null=True, editable=False
    )
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    date_created = models.DateTimeField(auto_now_add=True, editable=False)

    title = models.CharField(
        max_length=120, null=True, blank=True, default=None, editable=True
    )
    description = models.CharField(
        max_length=250, null=True, blank=True, default=None, editable=True
    )
    thumbnail = models.CharField(
        max_length=250, null=True, blank=True, default=None, editable=True
    )
    generated_thumbnail = models.CharField(
        max_length=250, null=True, blank=True, default=None, editable=True
    )
    thumbnail_image = models.ImageField(
        upload_to=user_directory_path, null=True, blank=True
    )

    fetched_page = models.TextField(max_length=60 * 1024, blank=True, editable=True)

    def __str__(self):
        return f"Fetch:{self.status}"


class Analysis(models.Model):
    """
    Stores data obtained after analysing the contents by a bot
    """

    submission = models.OneToOneField(
        Submission, on_delete=models.CASCADE, primary_key=True
    )
    status = models.CharField(
        max_length=10,
        choices=AnalysisStatuses.choices,
        default=AnalysisStatuses.PENDING,
        editable=True,
    )
    owner = models.ForeignKey(
        to=User, on_delete=models.SET_NULL, null=True, editable=False
    )
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    date_created = models.DateTimeField(auto_now_add=True, editable=False)

    summary = models.TextField(null=True, blank=True, default=None, editable=True)
    sentiment = models.TextField(null=True, blank=True, default=None, editable=True)

    def __str__(self) -> str:
        return f"Analysis:{self.status} ({self.owner})"


class Moderation(models.Model):
    """
    Stores posted details added by a moderator
    """

    submission = models.OneToOneField(
        Submission, on_delete=models.CASCADE, primary_key=True
    )

    status = models.CharField(
        max_length=10,
        choices=ModerationStatuses.choices,
        default=ModerationStatuses.PENDING,
        editable=True,
    )
    target_url = models.URLField(unique=True, blank=True, null=True, default=None)
    title = models.CharField(max_length=120, blank=True, null=True, default=None)
    description = models.CharField(max_length=250, blank=True, null=True, default=None)
    owner = models.ForeignKey(
        to=User,
        on_delete=models.SET_NULL,
        null=True,
        editable=False,
        related_name="moderations",
    )
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    date_created = models.DateTimeField(auto_now_add=True, editable=False)

    def __str__(self) -> str:
        return f"Mod:{self.status} ({self.owner})"


class Vote(models.Model):
    """Vote/rating provided by a user for a submitted item"""

    class Values(models.IntegerChoices):
        """Vote values are added when processing, so need to be numeric"""

        UP = 1, "👍"
        DOWN = -1, "👎"
        FLAG = -100, "💩"

    submission = models.ForeignKey(
        to=Submission,
        on_delete=models.CASCADE,
        null=False,
        editable=False,
        related_name="votes",
        blank=False,
    )
    owner = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        editable=True,  # only via admin
        related_name="votes",
    )
    value = models.SmallIntegerField(choices=Values.choices, default=Values.UP)

    last_updated = models.DateTimeField(auto_now=True, editable=False)
    date_created = models.DateTimeField(auto_now_add=True, editable=False)

    def __str__(self):
        return f"{self.id} ({self.owner},{self.submission},{self.value})"

    class Meta:
        unique_together = [("owner", "submission")]


# ---- Signal handlers that affect submission status


def set_status(submission: Submission, new_status: SubmissionStatuses):
    """Updates the status of a submission to the given one if it's needed and saves the model"""
    if submission.status != new_status:
        submission.status = new_status
        submission.save()


def calculate_status(submission: Submission):
    """Calculates the status of a submission based on all the related models that affect it.
    This will be called every time there is a relevant change (using signals)"""
    if hasattr(submission, "moderation"):
        moderation: Moderation = submission.moderation
        if moderation.status == ModerationStatuses.ACCEPTED:
            set_status(submission, SubmissionStatuses.ACCEPTED)
            return
        elif moderation.status == ModerationStatuses.REJECTED:
            set_status(submission, SubmissionStatuses.REJECTED_MOD)
            return
        else:
            # set this as basis unless others have more detail
            set_status(submission, SubmissionStatuses.PENDING)

    if hasattr(submission, "fetch"):
        fetchobj: Fetch = submission.fetch
        # only rejections change the main status
        if fetchobj.status == FetchStatuses.REJECTED_BANNED:
            set_status(submission, SubmissionStatuses.REJECTED_BANNED)
            return
        elif fetchobj.status == FetchStatuses.REJECTED_ERROR:
            set_status(submission, SubmissionStatuses.REJECTED_FETCH)
            return

    if hasattr(submission, "analysis"):
        analysis: Analysis = submission.analysis
        # only rejections change the main status
        if analysis.status == AnalysisStatuses.FAILED:
            set_status(submission, SubmissionStatuses.REJECTED_SENTIMENT)
            return


@receiver(post_save, sender=Moderation)
def moderation_changed(
    sender: Moderation,
    instance=None,
    created=False,
    **kwargs,  # pylint: disable=unused-argument
):
    """When moderation changes we may need to update the associated submission status"""
    calculate_status(instance.submission)


@receiver(post_save, sender=Fetch)
def fetch_changed(
    sender: Fetch,
    instance=None,
    created=False,
    **kwargs,  # pylint: disable=unused-argument
):
    """When moderation changes we may need to update the associated submission status"""
    calculate_status(instance.submission)


@receiver(post_save, sender=Analysis)
def analysis_changed(
    sender: Analysis,
    instance=None,
    created=False,
    **kwargs,  # pylint: disable=unused-argument
):
    """When moderation changes we may need to update the associated submission status"""
    calculate_status(instance.submission)
