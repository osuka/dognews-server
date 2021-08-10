# """ Test cases for Submission models """
# from test.common import ro_for, rw_for
# from django.contrib.auth.models import Group
# from django.test import TestCase
# from rest_framework import status
# from rest_framework.test import APITestCase
# from .models import Submission, ModeratedSubmission, Article
# from .test_submissions import sample_submission


# class ArticleModelTests(TestCase):
#     """
#     django model CRUD/logic tests
#     """

#     def setUp(self):
#         self.rw_user = rw_for([Submission, ModeratedSubmission, Article])
#         self.mod = rw_for([Submission, ModeratedSubmission, Article], "mod")

#     def test_create_submission_move_to_moderated_then_to_article(self):
#         """full lifecycle"""
#         submission: Submission = Submission.objects.create(
#             **sample_submission, owner=self.rw_user
#         )
#         moderated_submission: ModeratedSubmission = submission.move_to_moderation()
#         moderated_submission.status = ModeratedSubmission.Statuses.READY
#         moderated_submission.save()
#         article: Article = moderated_submission.move_to_article(self.mod)
#         self.assertEqual(Article.objects.count(), 1)
#         self.assertEqual(article.approver, self.mod)
#         self.assertEqual(article.moderated_submission.submission.owner, self.rw_user)


# # ------------------------------------------------------


# class ArticleAPITests(APITestCase):
#     """
#     External REST interface tests
#     """

#     def setUp(self):
#         self.rw_user = rw_for([Submission, ModeratedSubmission])
#         self.ro_user = ro_for([Submission, ModeratedSubmission])
#         self.rw_admin = rw_for(
#             [Submission, ModeratedSubmission], suffix="admin", admin=True
#         )
#         self.rw_mod = rw_for([Submission, ModeratedSubmission], suffix="mod")
#         group, _ = Group.objects.get_or_create(name="Moderators")
#         self.rw_mod.groups.add(group)

#     def as_user(self, user):
#         """ Peform remaining operations as a user that has the permission required """
#         self.client.force_authenticate(user)  # pylint: disable=no-member

#     def test_no_modify(self):
#         """ without authorization header, it """
#         response = self.client.post("/articles", {"anything": "blah blah"})
#         self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

#     def test_publicly_accessible(self):
#         """
#         GET /articles
#         GET /articles/1
#         """

#         tenth_article = None
#         for num in range(0, 50):
#             new_sub = {**sample_submission}
#             new_sub["target_url"] = sample_submission["target_url"] + f"{num}"
#             submission: Submission = Submission.objects.create(
#                 **new_sub, owner=self.rw_user
#             )
#             moderated_submission: ModeratedSubmission = submission.move_to_moderation()
#             moderated_submission.status = ModeratedSubmission.Statuses.READY
#             moderated_submission.save()
#             article: Article = moderated_submission.move_to_article(self.rw_mod)
#             if num == 10:
#                 tenth_article = article

#         response = self.client.get("/articles")
#         self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
#         self.assertEqual(len(response.data["results"]), Article.objects.count())

#         response = self.client.get(f"/articles/{tenth_article.id}")
#         self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
#         art = response.data
#         self.assertEqual(art["target_url"], sample_submission["target_url"] + "10")

#     def test_authenticated_accessible(self):
#         """GET /articles"""
#         for user in [self.rw_admin, self.rw_mod, self.rw_user, self.ro_user]:
#             self.as_user(user)
#             return self.test_publicly_accessible()

#     def test_no_modify_item(self):
#         """
#         DELETE /articles/1
#         PATCH /articles/1
#         UPDATE /articles/1
#         """
#         submission: Submission = Submission.objects.create(
#             **sample_submission, owner=self.rw_user
#         )
#         moderated_submission: ModeratedSubmission = submission.move_to_moderation()
#         moderated_submission.status = ModeratedSubmission.Statuses.READY
#         moderated_submission.save()
#         article: Article = moderated_submission.move_to_article(self.rw_mod)
#         for user in [self.rw_admin, self.rw_mod, self.rw_user, self.ro_user]:
#             self.as_user(user)
#             item_url = f"/articles/{article.id}"
#             response = self.client.delete(item_url)
#             self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
#             response = self.client.patch(item_url, {"target_url": "https://j.com"})
#             self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
#             response = self.client.patch(item_url, {"target_url": "https://j.com"})
#             self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
