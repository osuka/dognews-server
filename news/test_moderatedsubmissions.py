""" Test cases for Submission models """
from test.common import ro_for, rw_for
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Submission, ModeratedSubmission, Article


class ModeratedSubmissionModelTests(TestCase):
    """
    django model CRUD/logic tests
    """

    def setUp(self):
        self.rw_user = rw_for([Submission, ModeratedSubmission])

    def test_create_submission_move_to_moderated_then_to_article(self):
        """full lifecycle"""
        target = "https://google.com/1234"
        submission: Submission = Submission.objects.create(
            target_url=target,
            description="this is a submission",
            title="url title",
            owner=self.rw_user,
        )
        moderated_submission: ModeratedSubmission = submission.move_to_moderation()
        self.assertEqual(moderated_submission.status, ModeratedSubmission.Statuses.NEW)

        moderated_submission.move_to_article()
        self.assertEqual(
            Article.objects.filter(target_url=target).count(),
            0,
            "Item did moved to moderation in wrong state",
        )

        moderated_submission.status = ModeratedSubmission.Statuses.READY
        moderated_submission.save()
        moderated_submission.move_to_article()
        self.assertEqual(
            Article.objects.filter(target_url=target).count(),
            1,
            "Item did not move to moderation",
        )

        article: Article = Article.objects.get(target_url=target)
        self.assertEqual(article.status, Article.Statuses.VISIBLE)
        self.assertEqual(article.target_url, target)
        self.assertEqual(
            moderated_submission.status, ModeratedSubmission.Statuses.ACCEPTED
        )

        # Creating it twice does nothing
        article_two = moderated_submission.move_to_article()
        self.assertEqual(article, article_two)

    def test_rejected_items_cant_be_published(self):
        """We can't promote rejected items"""
        target = "https://google.com/1234"
        submission: Submission = Submission.objects.create(
            target_url=target,
            description="this is a submission",
            title="url title",
            owner=rw_for([Submission]),
        )
        moderated_submission: ModeratedSubmission = submission.move_to_moderation()
        moderated_submission.status = (
            ModeratedSubmission.Statuses.REJECTED_COULD_NOT_FETCH
        )
        moderated_submission.save()
        article: Article = moderated_submission.move_to_article()
        self.assertIsNone(article)


# ------------------------------------------------------


# class ModeratedSubmissionAPITests(APITestCase):
#     """
#     External REST interface tests
#     """

#     sample_submission = {
#         "target_url": "https://google.com",
#         "description": "this is a submission",
#         "title": "new idea",
#     }

#     def setUp(self):
#         self.rw_user = rw_for(Submission)
#         self.ro_user = ro_for(Submission)

#     def as_user(self, user):
#         """ Peform remaining operations as a user that has the permission required """
#         self.client.force_authenticate(user)  # pylint: disable=no-member

#     def test_default_unauthorized(self):
#         """ without authorization header, all is rejected """
#         endpoints = ["submissions"]
#         for model in endpoints:
#             response = self.client.post(
#                 f"/{model}", {"anything": "blah blah"}, follow=False
#             )
#             self.assertEqual(
#                 response.status_code, status.HTTP_401_UNAUTHORIZED, response.data
#             )

#     def test_testuser_create_item(self):
#         """Can create one item if the user has 'add' permission
#         POST /newsItem  --> 201
#         """
#         self.as_user(self.rw_user)
#         response = self.client.post("/submissions", self.sample_submission)
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
#         self.assertEqual(Submission.objects.count(), 1)
#         self.assertEqual(Submission.objects.get().target_url, "https://google.com")

#     def test_cannot_create_item(self):
#         """Can create one item if the user doesn't have the 'add' permission but is otherwise logged in
#         POST /newsItem  --> 403
#         """
#         self.as_user(self.ro_user)
#         response = self.client.post("/submissions", self.sample_submission)
#         self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)

#     def test_can_list_empty_items(self):
#         """Can list items if the user has 'view' permission when there are no items
#         GET /newsItem
#         """
#         self.as_user(self.ro_user)
#         response = self.client.get("/submissions")
#         self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
#         self.assertEqual(response.data["count"], 0)

#     def test_can_list_one_item(self):
#         """Can list items if the user has 'view' permission when there's one item
#         POST /newsItem
#         GET /newsItem
#         """
#         self.as_user(self.rw_user)
#         response = self.client.post("/submissions", self.sample_submission)
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

#         self.as_user(self.ro_user)
#         response = self.client.get("/submissions")
#         self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
#         self.assertEqual(response.data["count"], 1)
#         self.assertEqual(
#             response.data["results"][0]["target_url"], "https://google.com"
#         )

#     def test_can_paginate_items(self):
#         """Can list items and navigate throught them via pagination
#         POST /submissions  (*n)
#         GET /submissions
#         GET /submissions?offset=XXX
#         GET /submissions?offset=XXX
#         """
#         page_size = 50  # from settings.py, rest framework settings
#         self.as_user(self.rw_user)
#         for i in range(0, int(page_size * 2.5)):
#             item = self.sample_submission.copy()
#             item["target_url"] = f"https://google.com/?{i}"
#             response = self.client.post("/submissions", item)

#         # first page
#         self.as_user(self.ro_user)
#         response = self.client.get("/submissions", follow=True)
#         self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
#         self.assertEqual(response.data["count"], page_size * 2.5)
#         self.assertIn(f"limit={page_size}", response.data["next"])
#         self.assertIn(f"offset={page_size}", response.data["next"])
#         self.assertEqual(len(response.data["results"]), page_size)
#         self.assertEqual(
#             response.data["results"][0]["target_url"], "https://google.com/?0"
#         )

#         # second page
#         response = self.client.get(response.data["next"], follow=True)
#         self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
#         self.assertEqual(response.data["count"], page_size * 2.5)
#         self.assertIn(f"limit={page_size}", response.data["next"])
#         self.assertIn(f"offset={page_size * 2}", response.data["next"])
#         self.assertEqual(len(response.data["results"]), page_size)
#         self.assertEqual(
#             response.data["results"][0]["target_url"],
#             f"https://google.com/?{page_size}",
#         )

#         # third and last page
#         response = self.client.get(response.data["next"], follow=True)
#         self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
#         self.assertEqual(response.data["count"], page_size * 2.5)
#         self.assertIsNone(response.data["next"])
#         self.assertEqual(len(response.data["results"]), page_size * 0.5)
#         self.assertEqual(
#             response.data["results"][0]["target_url"],
#             f"https://google.com/?{2*page_size}",
#         )

#     def test_can_modify_item(self):
#         """Can modify a field of an item if the user has 'change' permission
#         POST /submissions   --> id
#         PATCH /submissions/<id>
#         GET /submissions
#         """
#         self.as_user(self.rw_user)
#         response = self.client.post("/submissions", self.sample_submission)
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

#         itemurl = response.data["url"]
#         response = self.client.patch(
#             f"{itemurl}",
#             {"target_url": "https://googlito.com"},
#             format="json",
#         )
#         self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
#         self.assertEqual(Submission.objects.count(), 1)
#         self.assertEqual(Submission.objects.get().target_url, "https://googlito.com")

#         itemurl = response.data["url"]
#         response = self.client.get(f"{itemurl}", format="json")
#         self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
#         self.assertEqual(response.data["target_url"], "https://googlito.com")

#     def test_cant_modify_readonlyfields(self):
#         """Can't modify a read onlyfield of an item even if the user has 'change' permission
#         POST /submissions   --> id
#         PATCH /submissions/<id>
#         GET /submissions
#         """
#         self.as_user(self.rw_user)
#         response = self.client.post("/submissions", self.sample_submission)
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

#         itemurl = response.data["url"]

#         response = self.client.patch(
#             f"{itemurl}",
#             {"owner": self.ro_user.pk},
#             format="json",
#         )

#         # rw fields are accepted but ignored by the serializer
#         self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
#         self.assertEqual(Submission.objects.count(), 1)
#         self.assertEqual(Submission.objects.get().target_url, "https://google.com")

#         itemurl = response.data["url"]
#         response = self.client.get(f"{itemurl}", format="json")
#         self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
#         self.assertEqual(
#             response.data["owner"], f"http://testserver/users/{self.rw_user.pk}"
#         )

#     def test_cant_do_anything_public(self):
#         """ A public user (unauthenticated) can't see anything """
#         self.as_user(self.rw_user)
#         response = self.client.post(
#             "/submissions", self.sample_submission, format="json"
#         )
#         itemurl = response.data["url"]
#         # item = Submission.objects.get(target_url=self.sample_submission["target_url"])
#         self.client.logout()
#         forbidden = ["/submissions", f"{itemurl}"]
#         for url in forbidden:
#             response = self.client.get(url)
#             self.assertEqual(
#                 response.status_code,
#                 status.HTTP_401_UNAUTHORIZED,
#                 f"Should not be able to access {url}",
#             )
