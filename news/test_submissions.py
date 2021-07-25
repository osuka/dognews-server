""" Test cases for Submission models """
from test.common import ro_for, rw_for
from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Submission, ModeratedSubmission

sample_submission = {
    "target_url": "https://google.com",
    "description": "this is a submission",
    "title": "new idea",
}


class SubmissionModelTests(TestCase):
    """
    django model CRUD and logic tests, independent from the external API
    """

    def test_create_item_and_move_to_moderation(self):
        """We can promote a submission object to moderated submission"""
        target = "https://google.com/1234"
        submission: Submission = Submission.objects.create(
            target_url=target,
            description="this is a submission",
            title="url title",
            owner=rw_for([Submission]),
        )
        submission.save()
        self.assertEqual(
            ModeratedSubmission.objects.filter(target_url=target).count(), 0
        )
        self.assertEqual(submission.status, Submission.Statuses.NEW)
        submission.move_to_moderation()
        self.assertEqual(
            ModeratedSubmission.objects.filter(target_url=target).count(),
            1,
            "Item did not move to moderation",
        )
        moderated_submission: ModeratedSubmission = ModeratedSubmission.objects.get(
            target_url=target
        )
        self.assertEqual(moderated_submission.status, ModeratedSubmission.Statuses.NEW)
        self.assertEqual(moderated_submission.target_url, target)
        self.assertEqual(submission.status, Submission.Statuses.ACCEPTED)

    def test_rejected_items_cant_be_moderated(self):
        """We can't promote rejected submissions"""
        target = "https://google.com/1234"
        submission: Submission = Submission.objects.create(
            target_url=target,
            description="this is a submission",
            title="url title",
            owner=rw_for([Submission]),
            status=Submission.Statuses.REJECTED_BLACKLISTED_DOMAIN,
        )
        self.assertRaises(ValidationError, submission.move_to_moderation)


# ------------------------------------------------------


class SubmissionAPITests(APITestCase):
    """
    External REST interface tests
    """

    def setUp(self):
        self.rw_user = rw_for([Submission])
        self.ro_user = ro_for([Submission])

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
        GET /newsItem
        """
        self.as_user(self.ro_user)
        response = self.client.get("/submissions")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["count"], 0)

    def test_can_list_one_item(self):
        """Can list items if the user has 'view' permission when there's one item
        POST /newsItem
        GET /newsItem
        """
        self.as_user(self.rw_user)
        response = self.client.post("/submissions", sample_submission)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

        self.as_user(self.ro_user)
        response = self.client.get("/submissions")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            response.data["results"][0]["target_url"], "https://google.com"
        )

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
            item = sample_submission.copy()
            item["target_url"] = f"https://google.com/?{i}"
            response = self.client.post("/submissions", item)

        # first page
        self.as_user(self.ro_user)
        response = self.client.get("/submissions", follow=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["count"], page_size * 2.5)
        self.assertIn(f"limit={page_size}", response.data["next"])
        self.assertIn(f"offset={page_size}", response.data["next"])
        self.assertEqual(len(response.data["results"]), page_size)
        first = int(page_size * 2.5) - 1
        self.assertEqual(
            response.data["results"][0]["target_url"],
            f"https://google.com/?{first}",
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
            f"https://google.com/?{first}",
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
            f"https://google.com/?{first}",
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
