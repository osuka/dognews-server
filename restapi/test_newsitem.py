"""
Tests for NewsItem model and associated views
"""
from random import random
from django.contrib.auth.models import User, Group, Permission
from rest_framework import status
from rest_framework.test import APITestCase
from .models import NewsItem

# Django rest framework testing reference:
# https://www.django-rest-framework.org/api-guide/testing/

# In settings.test we use sqlite (which is in-memory while testing)


class NewsItemTests(APITestCase):
    """
    Basic CRUD tests
    """

    sample_minimal_item = {
        'target_url': 'https://google.com',
        'source': 'newsitem_unit_test',
        'submitter': 'pytest',
        'title': 'new idea'
    }

    sample_with_ratings_item_without_user = {
        'target_url': 'https://www.google.com',
        'source': 'newsitem_unit_test',
        'submitter': 'pytest',
        'title': 'new idea',
        'ratings': [{
            'rating': 1
        }]
    }

    sample_with_ratings_item_with_user = {
        'target_url': 'https://www.google.com',
        'source': 'newsitem_unit_test',
        'submitter': 'pytest',
        'title': 'new idea',
        'ratings': [{
            'rating': 1,
            'user': 'can_delete'
        }]
    }

    def setUp(self):
        self.groups = {}
        self.users = {}
        for perm in ['add', 'change', 'view', 'delete']:
            self.groups[perm], _ = Group.objects.get_or_create(name=f'new_group{perm}')
            self.groups[perm].permissions.add(*Permission.objects.filter(
                content_type__model='newsitem', codename=f'{perm}_newsitem'))
            self.groups[perm].permissions.add(*Permission.objects.filter(
                content_type__model='rating', codename=f'{perm}_rating'))
            # ^ python note: star operator here unpacks the result into parameters
            self.users[perm] = User.objects.create_user(
                username=f'can_{perm}', email=f'nothing@example.com', password=f'x{random()}X')
            self.users[perm].groups.add(self.groups[perm])

    def as_user(self, perm):
        ''' Peform remaining operations as a user that has the permission required on newsitem '''
        self.client.force_authenticate(self.users[perm])  # pylint: disable=no-member

    def test_default_unauthorized(self):
        ''' without authorization header, all is rejected '''
        endpoints = ['newsItem', 'users', 'groups']
        for model in endpoints:
            response = self.client.get(f'/{model}', follow=True)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        for model in endpoints:
            response = self.client.post(
                f'/{model}', {'anything': 'blah blah'}, follow=False)
            self.assertEqual(response.status_code, status.HTTP_301_MOVED_PERMANENTLY)
            response = self.client.post(
                f'/{model}/', {'anything': 'blah blah'}, follow=True)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_can_create_item(self):
        ''' Can create one item if the user has 'add' permission
        '''
        self.as_user('add')
        response = self.client.post('/newsItem/', self.sample_minimal_item)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(NewsItem.objects.count(), 1)
        self.assertEqual(NewsItem.objects.get().target_url, 'https://google.com')

    def test_cannot_create_item(self):
        ''' Can create one item if the user doesn't have the 'add' permission but is otherwise logged in
        '''
        self.as_user('change')
        response = self.client.post('/newsItem/', self.sample_minimal_item)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_can_list_empty_items(self):
        ''' Can list items if the user has 'view' permission when there are no items
        '''
        self.as_user('view')
        response = self.client.get('/newsItem/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_can_list_one_item(self):
        ''' Can list items if the user has 'view' permission when there's one item
        '''
        self.as_user('add')
        response = self.client.post('/newsItem/', self.sample_minimal_item)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.as_user('view')
        response = self.client.get('/newsItem/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['target_url'], 'https://google.com')

    def test_can_paginate_items(self):
        ''' Can list items and navigate throught them via pagination
        '''
        page_size = 50  # from settings.py, rest framework settings
        self.as_user('add')
        for i in range(0, int(page_size * 2.5)):
            item = self.sample_minimal_item.copy()
            item['target_url'] = f'https://google.com/?{i}'
            response = self.client.post('/newsItem/', item)

        # first page
        self.as_user('view')
        response = self.client.get('/newsItem/', follow=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], page_size * 2.5)
        self.assertIn(f'limit={page_size}', response.data['next'])
        self.assertIn(f'offset={page_size}', response.data['next'])
        self.assertEqual(len(response.data['results']), page_size)
        self.assertEqual(response.data['results'][0]['target_url'], 'https://google.com/?0')

        # second page
        response = self.client.get(response.data['next'], follow=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], page_size * 2.5)
        self.assertIn(f'limit={page_size}', response.data['next'])
        self.assertIn(f'offset={page_size * 2}', response.data['next'])
        self.assertEqual(len(response.data['results']), page_size)
        self.assertEqual(response.data['results'][0]['target_url'],
                         f'https://google.com/?{page_size}')

        # third and last page
        response = self.client.get(response.data['next'], follow=True)
        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], page_size * 2.5)
        self.assertIsNone(response.data['next'])
        self.assertEqual(len(response.data['results']), page_size * 0.5)
        self.assertEqual(response.data['results'][0]['target_url'],
                         f'https://google.com/?{2*page_size}')

    def test_can_modify_item(self):
        ''' Can modify a field of an item if the user has 'change' permission
        '''
        self.as_user('add')
        response = self.client.post('/newsItem/', self.sample_minimal_item)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.as_user('change')
        print(response.data)
        itemurl = response.data['url']
        response = self.client.patch(f'{itemurl}', {
            'target_url': 'https://googlito.com',
        }, format='json')
        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(NewsItem.objects.count(), 1)
        self.assertEqual(NewsItem.objects.get().target_url, 'https://googlito.com')

    def test_can_add_item_with_ratings(self):
        ''' Can add a rating if the user has 'change' permission
        '''
        self.as_user('add')

        # response = self.client.post('/newsItem/', self.sample_minimal_item)
        response = self.client.post('/newsItem/', self.sample_with_ratings_item_without_user, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(NewsItem.objects.count(), 1)
        item = NewsItem.objects.get()
        self.assertIsNotNone(item.ratings.all()[0].user)
        self.assertEqual(item.ratings.all()[0].user.username, 'can_add')

    def test_can_add_ratings(self):
        ''' Can add a rating if the user has 'change' permission
        '''
        self.as_user('add')

        # response = self.client.post('/newsItem/', self.sample_minimal_item)
        response = self.client.post('/newsItem/', self.sample_minimal_item, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(NewsItem.objects.count(), 1)
        item = NewsItem.objects.get()
        self.assertEqual(item.ratings.count(), 0)

        itemurl = response.data['url']
        response = self.client.post(f'{itemurl}ratings/', {
            'rating': -1,
        }, format='json')
        print(response.request)
        print(response.data)

        self.assertEqual(NewsItem.objects.count(), 1)
        item = NewsItem.objects.get()
        self.assertIsNotNone(item.ratings)
        self.assertEqual(item.ratings.all()[0].rating, -1)
        self.assertEqual(item.ratings.all()[0].user.username, 'can_add')
