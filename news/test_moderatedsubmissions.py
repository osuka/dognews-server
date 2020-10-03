""" Test cases for Submission models """
from test.common import ro_for, rw_for
from django.core.exceptions import ValidationError
from django.contrib.auth.models import Group
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Submission, ModeratedSubmission, Article
from .test_submissions import sample_submission


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

        self.assertRaises(ValidationError, moderated_submission.move_to_article)
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
            owner=rw_for([Submission], "user2"),
        )
        moderated_submission: ModeratedSubmission = submission.move_to_moderation()
        moderated_submission.status = (
            ModeratedSubmission.Statuses.REJECTED_COULD_NOT_FETCH
        )
        moderated_submission.save()
        self.assertRaises(ValidationError, moderated_submission.move_to_article)
        self.assertEqual(Article.objects.count(), 0)


# ------------------------------------------------------


class ModeratedSubmissionAPITests(APITestCase):
    """
    External REST interface tests
    """

    def setUp(self):
        self.rw_user = rw_for([Submission, ModeratedSubmission])
        self.ro_user = ro_for([Submission, ModeratedSubmission])
        self.rw_admin = rw_for(
            [Submission, ModeratedSubmission], suffix="admin", admin=True
        )
        self.rw_mod = rw_for([Submission, ModeratedSubmission], suffix="mod")
        group, _ = Group.objects.get_or_create(name="Moderators")
        self.rw_mod.groups.add(group)

    def as_user(self, user):
        """ Peform remaining operations as a user that has the permission required """
        self.client.force_authenticate(user)  # pylint: disable=no-member

    def test_default_unauthorized(self):
        """ without authorization header, all is rejected """
        endpoints = ["moderatedsubmissions"]
        for model in endpoints:
            response = self.client.post(
                f"/{model}", {"anything": "blah blah"}, follow=False
            )
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cant_create_item(self):
        """Can't create one item even if the user has 'add' permission.
        The only way is to follow the life cycle submission -> mod submission
        POST /moderatedsubmission  --> 201
        """
        self.as_user(self.rw_user)
        response = self.client.post(
            "/moderatedsubmissions", {"target_url": "https://google.com/3342"}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)
        self.assertEqual(ModeratedSubmission.objects.count(), 0)

    def test_non_admins_can_see_them(self):
        """
        GET /moderatedsubmission  --> 200
        """
        self.as_user(self.rw_user)
        response = self.client.get("/moderatedsubmissions")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_non_admins_cant_patch_them(self):
        """
        PATCH /moderatedsubmission/{id}  --> 200
        """
        self.as_user(self.rw_user)
        response = self.client.get("/moderatedsubmissions")
        submission: Submission = Submission.objects.create(**sample_submission)
        moderated_submission: ModeratedSubmission = submission.move_to_moderation()
        response = self.client.get("/moderatedsubmissions")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(len(response.data["results"]), 1)
        [retrieved] = response.data["results"]

        response = self.client.patch(retrieved["url"], {"description": "oops"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        moderated_submission.refresh_from_db()
        self.assertEqual(
            moderated_submission.description, sample_submission["description"]
        )

    def test_admins_can_patch_them(self):
        """
        PATCH /moderatedsubmission/{id}  --> 200
        """
        self.as_user(self.rw_admin)
        response = self.client.get("/moderatedsubmissions")
        submission: Submission = Submission.objects.create(**sample_submission)
        moderated_submission: ModeratedSubmission = submission.move_to_moderation()
        response = self.client.get("/moderatedsubmissions")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(len(response.data["results"]), 1)
        [retrieved] = response.data["results"]

        response = self.client.patch(retrieved["url"], {"description": "oops"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        moderated_submission.refresh_from_db()
        self.assertEqual(moderated_submission.description, "oops")

    def test_admins_can_see_them(self):
        """
        GET /moderatedsubmission  --> 200
        """
        self.as_user(self.rw_admin)
        response = self.client.get("/moderatedsubmissions")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertListEqual(response.data["results"], [])
        submission: Submission = Submission.objects.create(**sample_submission)
        submission.move_to_moderation()
        response = self.client.get("/moderatedsubmissions")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(len(response.data["results"]), 1)
        [retrieved] = response.data["results"]
        self.assertEqual(retrieved["target_url"], sample_submission["target_url"])
        self.assertNotEqual(retrieved["date_created"], submission.date_created)

    def test_mods_modify_fields(self):
        """
        PATCH /moderatedsubmission/<id>  --> 200
        """
        self.as_user(self.rw_mod)
        submission: Submission = Submission.objects.create(**sample_submission)
        moderated_submission: ModeratedSubmission = submission.move_to_moderation()
        # modifying bot fields gots ignored
        response = self.client.patch(
            f"/moderatedsubmissions/{moderated_submission.id}",
            data={"bot_summary": "a summary"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        moderated_submission.refresh_from_db()
        self.assertIsNone(moderated_submission.bot_summary)

        # can modify target and description fields
        response = self.client.patch(
            f"/moderatedsubmissions/{moderated_submission.id}",
            data={
                "target_url": "https://yahoo.co.uk/11234",
                "description": "another desc",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        moderated_submission.refresh_from_db()
        self.assertEqual(moderated_submission.target_url, "https://yahoo.co.uk/11234")
        self.assertEqual(moderated_submission.description, "another desc")
