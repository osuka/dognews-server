# """
# Tests for NewsItem model and associated views
# """
# from random import random
# from django.shortcuts import get_object_or_404
# from django.contrib.auth.models import Group, Permission
# from django.contrib.auth import get_user_model
# from django.core.serializers import serialize
# from rest_framework import status
# from rest_framework.test import APITestCase
# from .models import NewsItem
# import json

# # Django rest framework testing reference:
# # https://www.django-rest-framework.org/api-guide/testing/

# # In settings.test we use sqlite (which is in-memory while testing)


# class NewsItemTests(APITestCase):
#     """
#     Basic CRUD tests
#     """

#     User = get_user_model()

#     sample_minimal_item = {
#         "target_url": "https://google.com",
#         "source": "newsitem_unit_test",
#         "title": "new idea",
#     }

#     sample_with_ratings_item_without_user = {
#         "target_url": "https://www.google.com",
#         "source": "newsitem_unit_test",
#         "title": "new idea",
#         "ratings": [{"rating": 1}],
#     }

#     sample_with_ratings_item_with_user = {
#         "target_url": "https://www.google.com",
#         "source": "newsitem_unit_test",
#         "title": "new idea",
#         "ratings": [{"rating": 1, "user": "testuser_delete"}],
#     }

#     rw_group = None
#     ro_group = None
#     admin_group = None
#     rw_user = None
#     rw_user_2 = None
#     ro_user = None
#     admin_user = None

#     def setUp(self):

#         # django caveat: we can't use the data that is populated during the migrations because we are in a transaction
#         # and that data hasn't been commited to db when they run, so eg Permissions aren't found

#         # we recreate the two groups: basic_users and admin  TODO: better way
#         # these give access to the model, there are other per-object permissions
#         allperms = Permission.objects.filter(
#             codename__in=[
#                 "view_newsitem",
#                 "add_newsitem",
#                 "change_newsitem",
#                 "delete_newsitem",
#                 "view_rating",
#                 "add_rating",
#                 "change_rating",
#                 "delete_rating",
#             ]
#         )

#         self.rw_group = Group.objects.create(name="test_basic_users")
#         self.rw_group.save()
#         self.rw_group.permissions.add(*allperms)

#         self.admin_group = Group.objects.create(name="test_admin")
#         self.admin_group.permissions.add(*allperms)
#         self.admin_group.save()

#         # for the test
#         self.ro_group = Group.objects.create(name="test_ro")
#         self.ro_group.save()
#         self.ro_group.permissions.add(
#             *Permission.objects.filter(codename__in=["view_newsitem", "view_rating"]),
#         )

#         self.rw_user = User.objects.create_user(
#             username=f"rw_user",
#             email=f"nothing@example.com",
#             password=f"x{random()}X",
#         )
#         self.rw_user.groups.add(self.rw_group)

#         self.rw_user_2 = User.objects.create_user(
#             username=f"rw_user_2",
#             email=f"nothing@example.com",
#             password=f"x{random()}X",
#         )
#         self.rw_user_2.groups.add(self.rw_group)

#         self.ro_user = User.objects.create_user(
#             username=f"ro_user",
#             email=f"nothing@example.com",
#             password=f"x{random()}X",
#         )
#         self.ro_user.groups.add(self.ro_group)

#         self.admin_user = User.objects.create_user(
#             username=f"admin_user",
#             email=f"nothing@example.com",
#             password=f"x{random()}X",
#         )
#         self.admin_user.groups.add(self.admin_group)

#     def as_user(self, user):
#         """ Peform remaining operations as a user that has the permission required on newsitem """
#         self.client.force_authenticate(user)

#     def test_default_unauthorized(self):
#         """ without authorization header, all is rejected """
#         endpoints = ["newsItem"]
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
#         response = self.client.post("/newsItem", self.sample_minimal_item)
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
#         self.assertEqual(NewsItem.objects.count(), 1)
#         self.assertEqual(NewsItem.objects.get().target_url, "https://google.com")

#     def test_cannot_create_item(self):
#         """Can create one item if the user doesn't have the 'add' permission but is otherwise logged in
#         POST /newsItem  --> 403
#         """
#         self.as_user(self.ro_user)
#         response = self.client.post("/newsItem", self.sample_minimal_item)
#         self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)

#     def test_can_list_empty_items(self):
#         """Can list items if the user has 'view' permission when there are no items
#         GET /newsItem
#         """
#         self.as_user(self.ro_user)
#         response = self.client.get("/newsItem")
#         self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
#         self.assertEqual(response.data["count"], 0)

#     def test_can_list_one_item(self):
#         """Can list items if the user has 'view' permission when there's one item
#         POST /newsItem
#         GET /newsItem
#         """
#         self.as_user(self.rw_user)
#         response = self.client.post("/newsItem", self.sample_minimal_item)
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

#         self.as_user(self.ro_user)
#         response = self.client.get("/newsItem")
#         self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
#         self.assertEqual(response.data["count"], 1)
#         self.assertEqual(
#             response.data["results"][0]["target_url"], "https://google.com"
#         )

#     def test_can_paginate_items(self):
#         """Can list items and navigate throught them via pagination
#         POST /newsItem  (*n)
#         GET /newsItem
#         GET /newsItem?offset=XXX
#         GET /newsItem?offset=XXX
#         """
#         page_size = 50  # from settings.py, rest framework settings
#         self.as_user(self.rw_user)
#         for i in range(0, int(page_size * 2.5)):
#             item = self.sample_minimal_item.copy()
#             item["target_url"] = f"https://google.com/?{i}"
#             response = self.client.post("/newsItem", item)

#         # first page
#         self.as_user(self.ro_user)
#         response = self.client.get("/newsItem", follow=True)
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
#         POST /newsItem   --> id
#         PATCH /newsItem/<id>
#         GET /newsItem
#         """
#         self.as_user(self.rw_user)
#         response = self.client.post("/newsItem", self.sample_minimal_item)
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

#         itemurl = response.data["url"]
#         response = self.client.patch(
#             f"{itemurl}",
#             {
#                 "target_url": "https://googlito.com",
#             },
#             format="json",
#         )
#         self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
#         self.assertEqual(NewsItem.objects.count(), 1)
#         self.assertEqual(NewsItem.objects.get().target_url, "https://googlito.com")

#         itemurl = response.data["url"]
#         response = self.client.get(f"{itemurl}", format="json")
#         self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
#         self.assertEqual(response.data["target_url"], "https://googlito.com")

#     def test_can_add_item_with_ratings(self):
#         """Can add a rating at the same time as a newsItem
#         POST /newsItem
#         """
#         self.as_user(self.rw_user)

#         response = self.client.post(
#             "/newsItem", self.sample_with_ratings_item_without_user, format="json"
#         )
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

#         item = NewsItem.objects.get(
#             target_url=self.sample_with_ratings_item_without_user["target_url"]
#         )
#         self.assertIsNotNone(item)
#         self.assertEqual(item.ratings.all()[0].rating, 1)
#         self.assertIsNotNone(item.ratings.all()[0].user)
#         self.assertEqual(item.ratings.all()[0].user.username, self.rw_user.username)

#     def test_can_add_ratings_to_item(self):
#         """Can add a rating to an existing news item
#         POST /newsItem
#         POST /newsItem/ratings
#         """
#         self.as_user(self.rw_user)

#         # response = self.client.post('/newsItem', self.sample_minimal_item)
#         response = self.client.post(
#             "/newsItem", self.sample_minimal_item, format="json"
#         )
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

#         item = NewsItem.objects.get(target_url=self.sample_minimal_item["target_url"])
#         self.assertEqual(item.ratings.count(), 0)

#         itemurl = response.data["url"]
#         response = self.client.post(
#             f"{itemurl}/ratings",
#             {
#                 "rating": -1,
#             },
#             format="json",
#         )

#         self.assertIsNotNone(item.ratings)
#         self.assertEqual(item.ratings.all()[0].rating, -1)
#         self.assertEqual(item.ratings.all()[0].user.username, "rw_user")

#     def test_can_change_own_ratings(self):
#         """Can change change a rating in an existing news item
#         POST /newsItem
#         PATCH /newsItem/<ID>/ratings/<ID>
#         POST /newsItem/<ID>/ratings    # automatically updates if necessary, based on request.user
#         """
#         self.as_user(self.rw_user)
#         response = self.client.post(
#             "/newsItem", self.sample_with_ratings_item_without_user, format="json"
#         )
#         item = NewsItem.objects.get(
#             target_url=self.sample_with_ratings_item_without_user["target_url"]
#         )
#         self.assertEqual(NewsItem.objects.count(), 1)

#         itemurl = response.data["url"]
#         response = self.client.patch(
#             f"{itemurl}/ratings/{item.ratings.all()[0].id}",
#             {
#                 "rating": 2,
#             },
#             format="json",
#         )
#         self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

#         # check
#         self.assertEqual(NewsItem.objects.count(), 1)
#         item = NewsItem.objects.get()
#         # item_as_json = serialize('json', NewsItem.objects.all())
#         # ratings_as_json = serialize('json', NewsItem.objects.all()[0].ratings.all())
#         self.assertEqual(item.ratings.count(), 1)
#         self.assertEqual(item.ratings.all()[0].rating, 2)
#         self.assertEqual(item.ratings.all()[0].user.username, self.rw_user.username)

#         # change without passing the ID directly (for own rating)
#         response = self.client.post(
#             f"{itemurl}/ratings",
#             {
#                 "rating": -1,
#             },
#             format="json",
#         )
#         self.assertEqual(
#             response.status_code, status.HTTP_200_OK, self.rw_user.username
#         )

#         # check
#         item = NewsItem.objects.get()
#         self.assertEqual(item.ratings.count(), 1)
#         self.assertEqual(item.ratings.all()[0].rating, -1)
#         self.assertEqual(item.ratings.all()[0].user.username, self.rw_user.username)

#     def test_cant_change_others_ratings(self):
#         """A User can't change another user's ratings
#         POST /newsItem    as rw_user
#         PATCH /newsItem/<ID>/ratings/<ID>   as rw_user_2 --> 403
#         """
#         self.as_user(self.rw_user)
#         response = self.client.post(
#             "/newsItem", self.sample_with_ratings_item_without_user, format="json"
#         )
#         item = NewsItem.objects.get(
#             target_url=self.sample_with_ratings_item_without_user["target_url"]
#         )
#         self.assertEqual(NewsItem.objects.count(), 1)

#         self.as_user(self.rw_user_2)
#         itemurl = response.data["url"]
#         response = self.client.patch(
#             f"{itemurl}/ratings/{item.ratings.all()[0].id}",
#             {
#                 "rating": 2,
#             },
#             format="json",
#         )
#         self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)

#     def test_can_delete_won_ratings(self):
#         """Can change change a rating in an existing news item
#         POST /newsItem
#         DELETE /newsItem/<ID>/ratings/<ID>
#         """
#         self.as_user(self.rw_user)
#         response = self.client.post(
#             "/newsItem", self.sample_with_ratings_item_without_user, format="json"
#         )
#         item = NewsItem.objects.get(
#             target_url=self.sample_with_ratings_item_without_user["target_url"]
#         )
#         self.assertEqual(NewsItem.objects.count(), 1)

#         itemurl = response.data["url"]
#         response = self.client.delete(f"{itemurl}/ratings/{item.ratings.all()[0].id}")
#         self.assertEqual(
#             response.status_code, status.HTTP_204_NO_CONTENT, response.data
#         )

#         # check
#         self.assertEqual(NewsItem.objects.count(), 1)
#         item = NewsItem.objects.get()
#         self.assertEqual(item.ratings.count(), 0)

#     def test_cant_delete_others_ratings(self):
#         """A user can't delete other users' ratings
#         POST /newsItem   as rw_user
#         DELETE /newsItem/<ID>/ratings/<ID>   as rw_user_2 --> 40
#         """
#         self.as_user(self.rw_user)
#         response = self.client.post(
#             "/newsItem", self.sample_with_ratings_item_without_user, format="json"
#         )
#         item = NewsItem.objects.get(
#             target_url=self.sample_with_ratings_item_without_user["target_url"]
#         )
#         self.assertEqual(NewsItem.objects.count(), 1)

#         self.as_user(self.rw_user_2)
#         itemurl = response.data["url"]
#         response = self.client.delete(f"{itemurl}/ratings/{item.ratings.all()[0].id}")
#         self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)

#     def test_cant_delete_all_ratings(self):
#         """A user can't delete other users' ratings
#         POST /newsItem   as rw_user
#         DELETE /newsItem/<ID>/ratings/<ID>   as rw_user_2 --> 40
#         """
#         self.as_user(self.rw_user)
#         response = self.client.post(
#             "/newsItem", self.sample_with_ratings_item_without_user, format="json"
#         )
#         itemurl = response.data["url"]

#         self.as_user(self.rw_user)
#         response = self.client.post(
#             f"{itemurl}/ratings",
#             {
#                 "rating": -1,
#             },
#             format="json",
#         )
#         self.as_user(self.rw_user_2)
#         response = self.client.post(
#             f"{itemurl}/ratings",
#             {
#                 "rating": 1,
#             },
#             format="json",
#         )

#         self.assertEqual(NewsItem.objects.count(), 1)
#         self.assertEqual(NewsItem.objects.all()[0].ratings.count(), 2)

#         response = self.client.delete(f"{itemurl}/ratings")
#         self.assertEqual(
#             response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED, response.data
#         )

#     def test_cant_do_anything_public(self):
#         """ A public user (unauthenticated) can't see anything """
#         self.as_user(self.rw_user)
#         response = self.client.post(
#             "/newsItem", self.sample_with_ratings_item_without_user, format="json"
#         )
#         itemurl = response.data["url"]
#         item = NewsItem.objects.get(
#             target_url=self.sample_with_ratings_item_without_user["target_url"]
#         )
#         ratingId = item.ratings.all()[0].id
#         self.client.logout()
#         forbidden = [
#             "/newsItem",
#             f"{itemurl}",
#             f"{itemurl}/ratings",
#             f"{itemurl}/ratings/{ratingId}",
#         ]
#         for url in forbidden:
#             response = self.client.get(url)
#             self.assertEqual(
#                 response.status_code,
#                 status.HTTP_401_UNAUTHORIZED,
#                 f"Should not be able to access {url}",
#             )
