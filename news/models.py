"""
Models to handle new submissions and their lifecycle to becoming Articles
"""

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


class Submission(models.Model):
    """
    Represents a submitted news item. This is produced by an authorized user
    (even if it's a bot). Items are processed once to fetch the information
    from the url and then are discarded or moved to the moderation queue
    """

    class Statuses(models.TextChoices):
        """Lifecycle status"""

        NEW = "new", "Processing"
        ACCEPTED = "accepted", "Moved to moderation"
        REJECTED_COULD_NOT_FETCH = "rej_fetch", "Rejected: Could not fetch"
        REJECTED_BLACKLISTED_DOMAIN = "rej_list", "Rejected: Blacklisted domain"
        REJECTED_MODERATOR = "rej_mod", "Rejected: Moderator action"

    target_url = models.URLField(unique=True)
    owner = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        editable=True,  # only via admin
        related_name="submissions",
    )
    title = models.CharField(max_length=120, blank=True, default="")
    description = models.CharField(max_length=250, blank=True, default="")
    date = models.DateTimeField(null=True, editable=True)
    status = models.CharField(
        max_length=10, choices=Statuses.choices, default=Statuses.NEW, editable=False
    )
    date_created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)

    # https://jodyboucher.com/blog/django-howto-null-blank-field-options
    fetched_page = models.TextField(max_length=60 * 1024, blank=True, editable=False)
    fetched_date = models.DateTimeField(null=True, editable=False)

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

    def move_to_moderation(self):
        """Create a ModeratedSubmission associated to this submission, and return it"""
        if self.status != self.Statuses.NEW and self.status != self.Statuses.ACCEPTED:
            raise ValidationError("Only non rejected submissions can be accepted")
        if self.status == self.Statuses.ACCEPTED:
            return ModeratedSubmission.objects.get(
                target_url=self.target_url
            )  # already done
        self.status = self.Statuses.ACCEPTED
        moderated_submission = ModeratedSubmission.objects.create(
            submission=self,
        )
        moderated_submission.save()
        self.save()
        return moderated_submission

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
        """Lifecycle status"""

        NEW = "new", "Processing"
        READY = "ready", "Ready for review"
        ACCEPTED = "accepted", "Published"
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

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
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
        super().save(force_insert, force_update, using, update_fields)

    def move_to_article(self, approver: User = None):
        """Create an Article associated with this instance, and return it.
        If called twice, it will return the already created object"""
        target_url = self.target_url if self.target_url else self.submission.target_url
        if self.status != self.Statuses.READY and self.status != self.Statuses.ACCEPTED:
            raise ValidationError("Only READY submissions can be moved")
        if self.status == self.Statuses.ACCEPTED:
            return Article.objects.get(target_url=target_url)  # already exists
        self.status = self.Statuses.ACCEPTED
        description = (
            self.description if self.description else self.submission.description
        )
        title = self.title if self.title else self.submission.title
        article = Article.objects.create(
            moderated_submission=self,
            target_url=target_url,
            title=title,
            description=description,
            thumbnail=self.thumbnail,
            submitter=self.submission.owner,
            approver=approver,
        )
        # article.save()
        self.save()
        return article

    def vote(self, user, vote_value):
        """Register a vote by a user - if it has already voted, the new vote
        replaces the vote value of the previous one"""
        vote, _ = self.votes.get_or_create(owner=user)
        if vote.value != vote_value:
            vote.value = vote_value
            vote.save()
        return vote

    # + ratings: is a one-to-many relation, see Rating
    def __str__(self):
        return f"{self.id} ({self.target_url[:20]})"


class Vote(models.Model):
    """Vote/rating provided by a user for a submitted item"""

    class Values(models.IntegerChoices):
        """Vote values are added when processing, so need to be numeric"""

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

    class Statuses(models.TextChoices):
        """Lifecycle status"""

        VISIBLE = "visible", "Visible"
        HIDDEN = "hidden", "Hidden (moderation action)"

    status = models.CharField(
        max_length=10, choices=Statuses.choices, default=Statuses.VISIBLE, editable=True
    )
    target_url = models.URLField(unique=True)
    title = models.CharField(max_length=120)
    description = models.CharField(max_length=512)
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
    approver = models.ForeignKey(
        to=User,
        on_delete=models.SET_NULL,
        null=True,
        editable=False,
        related_name="approved_articles",
    )

    last_updated = models.DateTimeField(auto_now=True, editable=False)
    date_created = models.DateTimeField(auto_now_add=True, editable=False)

    def __str__(self):
        return f"{self.id} ({self.target_url[:20]},{self.date_created})"
