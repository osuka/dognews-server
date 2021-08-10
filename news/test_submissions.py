""" Test cases for Submission models """
from test.common import ro_for, rw_for
from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase
from .models import (
    Fetch,
    FetchStatuses,
    ModerationStatuses,
    Submission,
    Moderation,
    SubmissionStatuses,
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


class SubmissionModelTests(TestCase):
    """
    django model CRUD and logic tests, independent from the external API
    """

    def test_changing_moderation_changes_status(self):
        """Status of the parent submission is updated based on modifications made to related objects"""
        target = "https://google.com/1234"
        submission: Submission = Submission.objects.create(
            target_url=target,
            description="this is a submission",
            title="url title",
            owner=rw_for([Submission]),
        )
        submission.save()
        self.assertEqual(Moderation.objects.filter(target_url=target).count(), 0)
        self.assertEqual(submission.status, SubmissionStatuses.PENDING)
        mod = Moderation(submission=submission, status=ModerationStatuses.ACCEPTED)
        mod.save()
        self.assertEqual(submission.status, SubmissionStatuses.ACCEPTED)
        mod.status = ModerationStatuses.REJECTED
        mod.save()
        self.assertEqual(submission.status, SubmissionStatuses.REJECTED_MOD)

    def test_changing_fetched_accepted_doesnt_change_submission_status(self):
        """When a bot changes the status to 'fetched' the status of the submission
        doesn't change status if it was accepted
        but if the bot set it to rejected then it does change the status"""
        target = "https://google.com/1234"
        submission: Submission = Submission.objects.create(
            target_url=target,
            description="this is a submission",
            title="url title",
            owner=rw_for([Submission]),
        )
        submission.save()
        self.assertEqual(submission.status, SubmissionStatuses.PENDING)

        fetching = Fetch(submission=submission, status=FetchStatuses.FETCHED)
        fetching.save()
        self.assertEqual(submission.status, SubmissionStatuses.PENDING)

        fetching.status = FetchStatuses.REJECTED_BANNED
        fetching.save()
        self.assertEqual(submission.status, SubmissionStatuses.REJECTED_BANNED)

        fetching.status = FetchStatuses.REJECTED_ERROR
        fetching.save()
        self.assertEqual(submission.status, SubmissionStatuses.REJECTED_FETCH)


# ------------------------------------------------------


class SubmissionAPITests(APITestCase):
    """
    External REST interface tests
    """

    def setUp(self):
        self.rw_user = rw_for([Submission], "user1")
        self.rw_user2 = rw_for([Submission], "user2")
        self.ro_user = ro_for([Submission], "user_ro")
        self.rw_mod = rw_for([Submission, Moderation], "mod1")
        self.rw_mod2 = rw_for([Submission, Moderation], "mod2")

    def as_user(self, user):
        """Peform remaining operations as a user that has the permission required"""
        self.client.force_authenticate(user)  # pylint: disable=no-member

    def test_default_unauthorized(self):
        """without authorization header, all is rejected"""
        endpoints = ["submissions"]
        for model in endpoints:
            response = self.client.post(
                f"/{model}", {"anything": "blah blah"}, follow=False
            )
            self.assertEqual(
                response.status_code, status.HTTP_401_UNAUTHORIZED, response.data
            )

    def test_testuser_create_item(self):
        """Can create one item if the user has 'add' permission
        POST /newsItem  --> 201
        """
        self.as_user(self.rw_user)
        response = self.client.post("/submissions", sample_submission)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(Submission.objects.count(), 1)
        self.assertEqual(Submission.objects.get().target_url, "https://google.com")

    def test_cannot_create_item(self):
        """Can create one item if the user doesn't have the 'add' permission but is otherwise logged in
        POST /newsItem  --> 403
        """
        self.as_user(self.ro_user)
        response = self.client.post("/submissions", sample_submission)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)

    def test_can_list_empty_items(self):
        """Can list items if the user has 'view' permission when there are no items
        GET /submission
        """
        self.as_user(self.ro_user)
        response = self.client.get("/submissions")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["count"], 0)

    def test_can_list_only_theirs_item(self):
        """One user can list their items but a different user that isn't
        a moderator can't list them env if the user has 'view' permission when there's one item
        POST /submissions
        GET /submissions
        """
        # user 1 has 3 submissions
        sub1 = [
            make_submission("http://localhost/number1_1"),
            make_submission("http://localhost/number1_2"),
            make_submission("http://localhost/number1_3"),
        ]

        # user 2 has 2 submission
        sub2 = [
            make_submission("http://localhost/number2_1"),
            make_submission("http://localhost/number2_2"),
        ]

        self.as_user(self.rw_user)
        for sub in sub1:
            response = self.client.post("/submissions", sub)
            self.assertEqual(
                response.status_code, status.HTTP_201_CREATED, response.data
            )

        self.as_user(self.rw_user2)
        for sub in sub2:
            response = self.client.post("/submissions", sub)
            self.assertEqual(
                response.status_code, status.HTTP_201_CREATED, response.data
            )

        self.as_user(self.rw_user)  # first user: sees their 3
        response = self.client.get("/submissions")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["count"], 3)
        self.assertEqual(
            response.data["results"][0]["target_url"], sub1[0]["target_url"]
        )

        self.as_user(self.rw_user2)  # second user: seeis their 2
        response = self.client.get("/submissions")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(
            response.data["results"][1]["target_url"], sub2[1]["target_url"]
        )

        self.as_user(self.ro_user)  # different user altogether, sees nothing
        response = self.client.get("/submissions")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["count"], 0)

        self.as_user(self.rw_mod)  # mod: sees all
        response = self.client.get("/submissions")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["count"], 5)

    def test_can_paginate_items(self):
        """Can list items and navigate throught them via pagination
        POST /submissions  (*n)
        GET /submissions
        GET /submissions?offset=XXX
        GET /submissions?offset=XXX
        """
        page_size = 50  # from settings.py, rest framework settings
        self.as_user(self.rw_user)
        for i in range(0, int(page_size * 2.5)):
            response = self.client.post(
                "/submissions", make_submission(f"https://localhost/?{i}")
            )

        # first page
        self.as_user(self.rw_user)  # same user
        response = self.client.get("/submissions?ordering=-date_created", follow=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["count"], page_size * 2.5)
        self.assertIn(f"limit={page_size}", response.data["next"])
        self.assertIn(f"offset={page_size}", response.data["next"])
        self.assertEqual(len(response.data["results"]), page_size)
        first = int(page_size * 2.5) - 1
        self.assertEqual(
            response.data["results"][0]["target_url"],
            f"https://localhost/?{first}",
        )

        # second page
        response = self.client.get(response.data["next"], follow=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["count"], page_size * 2.5)
        self.assertIn(f"limit={page_size}", response.data["next"])
        self.assertIn(f"offset={page_size * 2}", response.data["next"])
        self.assertEqual(len(response.data["results"]), page_size)
        first = first - page_size  # is in reverse order
        self.assertEqual(
            response.data["results"][0]["target_url"],
            f"https://localhost/?{first}",
        )

        # third and last page
        response = self.client.get(response.data["next"], follow=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["count"], page_size * 2.5)
        self.assertIsNone(response.data["next"])
        self.assertEqual(len(response.data["results"]), page_size * 0.5)
        first = first - page_size
        self.assertEqual(
            response.data["results"][0]["target_url"],
            f"https://localhost/?{first}",
        )

    def test_can_modify_item(self):
        """Can modify a field of an item if the user has 'change' permission
        POST /submissions   --> id
        PATCH /submissions/<id>
        GET /submissions
        """
        self.as_user(self.rw_user)
        response = self.client.post("/submissions", sample_submission)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

        itemurl = response.data["url"]
        response = self.client.patch(
            f"{itemurl}",
            {"target_url": "https://googlito.com"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(Submission.objects.count(), 1)
        self.assertEqual(Submission.objects.get().target_url, "https://googlito.com")

        itemurl = response.data["url"]
        response = self.client.get(f"{itemurl}", format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["target_url"], "https://googlito.com")

    def test_cant_modify_readonlyfields(self):
        """Can't modify a read onlyfield of an item even if the user has 'change' permission
        POST /submissions   --> id
        PATCH /submissions/<id>
        GET /submissions
        """
        self.as_user(self.rw_user)
        response = self.client.post("/submissions", sample_submission)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

        itemurl = response.data["url"]

        response = self.client.patch(
            f"{itemurl}",
            {"owner": self.ro_user.pk},
            format="json",
        )

        # rw fields are accepted but ignored by the serializer
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(Submission.objects.count(), 1)
        self.assertEqual(Submission.objects.get().target_url, "https://google.com")

        itemurl = response.data["url"]
        response = self.client.get(f"{itemurl}", format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(
            response.data["owner"], f"http://testserver/users/{self.rw_user.pk}"
        )

    def test_cant_do_anything_public(self):
        """A public user (unauthenticated) can't see anything"""
        self.as_user(self.rw_user)
        response = self.client.post("/submissions", sample_submission, format="json")
        itemurl = response.data["url"]
        # item = Submission.objects.get(target_url=sample_submission["target_url"])
        self.client.logout()
        forbidden = ["/submissions", f"{itemurl}"]
        for url in forbidden:
            response = self.client.get(url)
            self.assertEqual(
                response.status_code,
                status.HTTP_401_UNAUTHORIZED,
                f"Should not be able to access {url}",
            )
