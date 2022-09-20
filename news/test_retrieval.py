"""
Test cases for Retrieval models

Retrieval is a sub model of Submission, with a 1-1 relation

"""
from io import BytesIO
from test.common import ro_for, rw_for
from PIL import Image
from django.core.files import File
from django.core.files.images import ImageFile
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase
from .models import (
    Retrieval,
    RetrievalStatuses,
    ModerationStatuses,
    Submission,
    Moderation,
    SubmissionStatuses,
    Vote,
)

sample_submission = {
    "target_url": "https://google.com",
    "description": "this is a submission",
    "title": "new idea",
}


def make_submission(target_url: str):
    """Returns a new sample submission object with the given url"""
    submission = sample_submission.copy()
    submission["target_url"] = target_url
    return submission


class RetrievalTests(TestCase):
    """
    django model CRUD and logic tests, independent from the external API
    """

    test_image_file = "test/resources/Test-Logo-Small-Black-transparent-1.png"

    def test_newly_created_submission_has_no_retrieval(self):
        """When a submission is created it should not have a retrieval object"""
        target = "https://google.com/1234"
        submission: Submission = Submission.objects.create(
            target_url=target,
            description="this is a submission",
            title="url title",
            owner=rw_for([Submission]),
        )
        submission.save()
        self.assertFalse(hasattr(submission, "retrieval"))
        self.assertEqual(Retrieval.objects.count(), 0)

    def test_newly_created_submission_can_be_fetched(self):
        """When a submission is created it should not have a retrieval object"""
        target = "https://google.com/1234"
        submission: Submission = Submission.objects.create(
            target_url=target,
            description="this is a submission",
            title="url title",
            owner=rw_for([Submission]),
        )
        submission.save()
        self.assertFalse(hasattr(submission, "retrieval"))
        submission.retrieval = Retrieval(
            submission=submission, status=RetrievalStatuses.FETCHED
        )

        # one has to save the retrieval object to see it
        submission2: Submission = Submission.objects.get(target_url=target)
        self.assertFalse(hasattr(submission2, "retrieval"))

        # saving the original object does nothing
        submission.save()
        submission2 = Submission.objects.get(target_url=target)
        self.assertFalse(hasattr(submission2, "retrieval"))

        # there is retrieval created on the database
        self.assertEqual(Retrieval.objects.count(), 0)

        # saving the 'retrieval' object is what actually stores it
        submission.retrieval.save()
        submission2 = Submission.objects.get(target_url=target)
        self.assertTrue(hasattr(submission2, "retrieval"))
        self.assertEqual(Retrieval.objects.count(), 1)

    def test_retrieval_can_be_updated(self):
        """The retrieval object is meant to be updated by external bots/API calls,
        but can also be edited via the admin UI"""
        target = "https://google.com/1234"
        submission: Submission = Submission.objects.create(
            target_url=target,
            description="this is a submission",
            title="url title",
            owner=rw_for([Submission]),
        )
        submission.save()
        self.assertIsNone(Retrieval.objects.first())

        submission.retrieval = Retrieval(
            submission=submission, status=RetrievalStatuses.FETCHED
        )
        submission.retrieval.save()

        submission2: Submission = Submission.objects.get(target_url=target)
        submission2.retrieval.status = RetrievalStatuses.REJECTED_BANNED
        submission2.retrieval.save()
        # db is updated
        self.assertEqual(
            Retrieval.objects.first().status, RetrievalStatuses.REJECTED_BANNED
        )

        # but note that objects are not reloaded automatically
        self.assertEqual(submission.retrieval.status, RetrievalStatuses.FETCHED)

        # a call to refresh to the parent object it manually is needed
        submission.refresh_from_db()
        self.assertEqual(submission.retrieval.status, RetrievalStatuses.REJECTED_BANNED)

    def test_retrieval_can_have_a_page_thumbnail_uploaded(self):
        """Thumbnails are image objects (ImageField)"""
        target = "https://google.com/1234"
        submission: Submission = Submission.objects.create(
            target_url=target,
            description="this is a submission",
            title="url title",
            owner=rw_for([Submission]),
        )
        submission.save()
        self.assertIsNone(Retrieval.objects.first())

        # saving an image needs to be done via ImageFile (or Image?)
        submission.retrieval = Retrieval(
            submission=submission, status=RetrievalStatuses.FETCHED
        )
        with open(self.test_image_file, "rb") as image_file:
            # with ImageFile it knows the name and type etc
            submission.retrieval.thumbnail_from_page = ImageFile(image_file)
            submission.retrieval.save()

        # the only way to test if an ImageField is not defined seems to be this
        # bool(submission.retrieval.thumbnail_processed) is False)
        self.assertFalse(submission.retrieval.thumbnail_processed)
        self.assertFalse(submission.retrieval.thumbnail_submitted)
        self.assertTrue(submission.retrieval.thumbnail_from_page)

        self.assertIsNotNone(submission.retrieval.thumbnail_from_page.file)

        # cleanup, files are being saved in public/media
        submission.retrieval.thumbnail_from_page.delete(save=True)

    def test_retrieval_can_have_a_page_thumbnail_generated(self):
        """Thumbnails are image objects (ImageField)"""
        target = "https://google.com/1234"
        submission: Submission = Submission.objects.create(
            target_url=target,
            description="this is a submission",
            title="url title",
            owner=rw_for([Submission]),
        )
        submission.save()
        self.assertIsNone(Retrieval.objects.first())

        # saving an image from an inmemory one
        image: Image = Image.open(self.test_image_file)
        # original image is 2480 x 2480
        img_reduced = image.crop((100, 100, 300, 300))
        submission.retrieval = Retrieval(
            submission=submission, status=RetrievalStatuses.FETCHED
        )
        # image has to be saved into a blob first to set format etc
        # https://stackoverflow.com/questions/49064705/save-a-generated-pil-image-into-an-imagefield-in-django
        blob = BytesIO()
        img_reduced.save(blob, "PNG")
        # with Image it can't know the name or image type
        submission.retrieval.thumbnail_from_page.save(
            "test/generated.png", File(blob), save=False
        )
        submission.retrieval.save()

        # the only way to test if an ImageField is not defined seems to be this
        # bool(submission.retrieval.thumbnail_processed) is False)
        self.assertFalse(submission.retrieval.thumbnail_processed)
        self.assertFalse(submission.retrieval.thumbnail_submitted)
        self.assertTrue(submission.retrieval.thumbnail_from_page)

        self.assertIsNotNone(submission.retrieval.thumbnail_from_page.file)

        # cleanup, files are being saved in public/media
        submission.retrieval.thumbnail_from_page.delete(save=True)
