""" Test cases for Submission models """
from test.common import ro_for, rw_for
from django.db.utils import IntegrityError
from django.contrib.auth.models import Group
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Submission, ModeratedSubmission, Vote
from .test_submissions import sample_submission

# pylint: disable=missing-function-docstring


class VoteModelTests(TestCase):
    """
    django model CRUD/logic tests
    """

    def setUp(self):
        self.user = ro_for([])
        self.rw_user = rw_for([Submission], "user2")

    def test_can_create_vote_entities(self):
        """any authenticated user can vote"""
        submission: Submission = Submission.objects.create(**sample_submission)
        moderated_submission: ModeratedSubmission = submission.move_to_moderation()
        moderated_submission.votes.add(
            Vote.objects.create(value=Vote.Values.UP, owner=self.rw_user)
        )
        # can't add twice for same user
        self.assertRaises(
            IntegrityError,
            lambda: moderated_submission.votes.add(
                Vote.objects.create(value=Vote.Values.DOWN, owner=self.rw_user)
            ),
        )

    def test_can_vote_via_subms(self):
        """any authenticated user can vote multiple times, but only one vote is kept"""
        submission: Submission = Submission.objects.create(**sample_submission)
        moderated_submission: ModeratedSubmission = submission.move_to_moderation()
        for value in [Vote.Values.DOWN, Vote.Values.UP, Vote.Values.FLAG]:
            moderated_submission.vote(self.rw_user, value)
            moderated_submission.refresh_from_db()
            self.assertEqual(moderated_submission.votes.count(), 1)
            self.assertEqual(moderated_submission.votes.first().value, value)


# ------------------------------------------------------


class VoteAPITests(APITestCase):
    """
    External REST interface tests
    """

    def setUp(self):
        self.poster_user = rw_for([Submission, Vote], suffix="poster")
        self.normal_user = rw_for([Vote], suffix="normal")
        self.ro_user = ro_for([ModeratedSubmission, Vote], suffix="onlyread")
        self.moderator1 = rw_for([Submission, ModeratedSubmission, Vote], suffix="mod1")
        self.moderator2 = rw_for([Submission, ModeratedSubmission, Vote], suffix="mod2")
        self.admin = rw_for(
            [Submission, ModeratedSubmission, Vote], suffix="admin", admin=True
        )
        group, _ = Group.objects.get_or_create(name="Moderators")
        self.moderator1.groups.add(group)
        self.moderator2.groups.add(group)

    def as_user(self, user):
        """ Peform remaining operations as a user that has the permission required """
        self.client.force_authenticate(user)  # pylint: disable=no-member

    def test_default_unauthorized(self):
        """ without authorization header, all is rejected """

        # a non-existend submission ID
        response = self.client.post(
            "/moderatedsubmissions/4324311/votes", data={}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # an existing submission ID
        moderated_submission = self._create()
        response = self.client.post(
            f"/moderatedsubmissions/{moderated_submission.pk}/votes",
            data={"value": Vote.Values.UP},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # listing
        response = self.client.get(
            f"/moderatedsubmissions/{moderated_submission.pk}/votes"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # deleting existing vote ID
        vote = moderated_submission.vote(self.poster_user, Vote.Values.DOWN)
        response = self.client.post(
            f"/votes/{vote.pk}",
            data={"value": Vote.Values.UP},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def _create(self) -> ModeratedSubmission:
        # add random ones with votes and stuff
        for suffix in ["-uno", "-dos", "-tres", "-cuatro"]:
            submission: Submission = Submission.objects.create(
                target_url=sample_submission["target_url"] + suffix,
                description=sample_submission["description"] + suffix,
                title=sample_submission["title"] + suffix,
                owner=self.poster_user,
            )
            my_mod = submission.move_to_moderation()
            # helps make sure votes for other stuff aren't returned when querying one
            my_mod.vote(self.admin, Vote.Values.FLAG)

        submission: Submission = Submission.objects.create(
            **sample_submission, owner=self.poster_user
        )
        return submission.move_to_moderation()

    def test_a_poster_can_vote_its_own_submission(self):
        moderated_submission: ModeratedSubmission = self._create()
        self.assertEqual(moderated_submission.votes.count(), 0)
        self.as_user(self.poster_user)
        response = self.client.post(
            f"/moderatedsubmissions/{moderated_submission.pk}/votes",
            {"value": Vote.Values.UP},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(moderated_submission.votes.count(), 1)
        self.assertEqual(moderated_submission.votes.first().value, Vote.Values.UP)
        self.assertEqual(moderated_submission.votes.first().owner, self.poster_user)

    def test_a_user_can_vote_others_submission(self):
        moderated_submission: ModeratedSubmission = self._create()
        self.assertEqual(moderated_submission.votes.count(), 0)
        self.as_user(self.normal_user)
        response = self.client.post(
            f"/moderatedsubmissions/{moderated_submission.pk}/votes",
            {"value": Vote.Values.UP},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(moderated_submission.votes.count(), 1)
        self.assertEqual(moderated_submission.votes.first().value, Vote.Values.UP)
        self.assertEqual(moderated_submission.votes.first().owner, self.normal_user)

    def test_a_user_can_remove_their_own_vote(self):
        moderated_submission: ModeratedSubmission = self._create()
        self.assertEqual(moderated_submission.votes.count(), 0)
        self.as_user(self.normal_user)
        response = self.client.post(
            f"/moderatedsubmissions/{moderated_submission.pk}/votes",
            {"value": Vote.Values.UP},
            format="json",
        )
        self.assertEqual(Vote.objects.count(), 5)
        self.assertEqual(moderated_submission.votes.count(), 1)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.delete(response.data["url"])
        self.assertEqual(moderated_submission.votes.count(), 0)  # deleted it
        self.assertEqual(Vote.objects.count(), 4)  # and only it

    def test_an_admin_can_remove_someones_vote(self):
        moderated_submission: ModeratedSubmission = self._create()
        moderated_submission.vote(self.normal_user, Vote.Values.DOWN)
        vote = moderated_submission.vote(self.poster_user, Vote.Values.UP)
        self.assertEqual(moderated_submission.votes.count(), 2)
        self.assertEqual(Vote.objects.count(), 6)
        self.as_user(self.admin)
        response = self.client.delete(f"/votes/{vote.pk}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(moderated_submission.votes.count(), 1)  # deleted it
        self.assertEqual(Vote.objects.count(), 5)  # and only it

    def test_a_mod_can_remove_someones_vote(self):
        moderated_submission: ModeratedSubmission = self._create()
        vote = moderated_submission.vote(self.poster_user, Vote.Values.UP)
        self.as_user(self.moderator2)
        response = self.client.delete(f"/votes/{vote.pk}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(moderated_submission.votes.count(), 0)  # deleted it

    def test_a_mod_can_vote_others_submission(self):
        moderated_submission: ModeratedSubmission = self._create()
        self.assertEqual(moderated_submission.votes.count(), 0)
        self.as_user(self.moderator1)
        response = self.client.post(
            f"/moderatedsubmissions/{moderated_submission.pk}/votes",
            {"value": Vote.Values.UP},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(moderated_submission.votes.count(), 1)
        self.assertEqual(moderated_submission.votes.first().value, Vote.Values.UP)
        self.assertEqual(moderated_submission.votes.first().owner, self.moderator1)

    def test_all_users_can_see_all_votes(self):
        moderated_submission: ModeratedSubmission = self._create()
        moderated_submission.vote(self.moderator1, Vote.Values.DOWN)
        moderated_submission.vote(self.moderator2, Vote.Values.FLAG)
        moderated_submission.vote(self.poster_user, Vote.Values.UP)
        moderated_submission.vote(self.normal_user, Vote.Values.UP)
        self.assertEqual(moderated_submission.votes.count(), 4)
        self.as_user(self.ro_user)
        response = self.client.get(
            f"/moderatedsubmissions/{moderated_submission.pk}/votes"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 4)
        expected_results = [
            (Vote.Values.DOWN, f"http://testserver/users/{self.moderator1.pk}"),
            (Vote.Values.FLAG, f"http://testserver/users/{self.moderator2.pk}"),
            (Vote.Values.UP, f"http://testserver/users/{self.poster_user.pk}"),
            (Vote.Values.UP, f"http://testserver/users/{self.normal_user.pk}"),
        ]
        for num in range(0, 3):
            self.assertEqual(
                (
                    response.data["results"][num]["value"],
                    response.data["results"][num]["owner"],
                ),
                expected_results[num],
            )

    def test_multiple_votes_same_user(self):
        moderated_submission: ModeratedSubmission = self._create()
        self.assertEqual(moderated_submission.votes.count(), 0)
        self.as_user(self.poster_user)
        response = self.client.post(
            f"/moderatedsubmissions/{moderated_submission.pk}/votes",
            {"value": Vote.Values.UP},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(moderated_submission.votes.count(), 1)
        self.assertEqual(moderated_submission.votes.first().value, Vote.Values.UP)
        self.assertEqual(moderated_submission.votes.first().owner, self.poster_user)

        # cast a different vote
        response = self.client.post(
            f"/moderatedsubmissions/{moderated_submission.pk}/votes",
            {"value": Vote.Values.DOWN},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(moderated_submission.votes.count(), 1)
        self.assertEqual(moderated_submission.votes.first().value, Vote.Values.DOWN)

    def test_multiple_users_voting(self):
        moderated_submission: ModeratedSubmission = self._create()
        self.assertEqual(moderated_submission.votes.count(), 0)
        self.as_user(self.poster_user)
        response = self.client.post(
            f"/moderatedsubmissions/{moderated_submission.pk}/votes",
            {"value": Vote.Values.UP},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # cast a different vote
        response = self.client.post(
            f"/moderatedsubmissions/{moderated_submission.pk}/votes",
            {"value": Vote.Values.DOWN},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # another user casts a vote
        self.as_user(self.normal_user)
        response = self.client.post(
            f"/moderatedsubmissions/{moderated_submission.pk}/votes",
            {"value": Vote.Values.UP},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(moderated_submission.votes.count(), 2)
        self.assertEqual(
            [
                (v.owner, v.value)
                for v in moderated_submission.votes.all().order_by("owner")
            ],
            [(self.poster_user, Vote.Values.DOWN), (self.normal_user, Vote.Values.UP)],
        )
