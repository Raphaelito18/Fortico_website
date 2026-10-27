from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.content.models import Expertise


class ExpertiseApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_public_list_only_contains_published_content(self):
        Expertise.objects.create(title='Publié', summary='Visible publiquement', is_published=True)
        Expertise.objects.create(title='Brouillon', summary='Visible après connexion', is_published=False)

        response = self.client.get('/api/v1/expertises/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item['title'] for item in response.data['results']], ['Publié'])

    def test_anonymous_user_cannot_create_expertise(self):
        response = self.client.post(
            '/api/v1/expertises/',
            {'title': 'Non autorisé', 'summary': 'Création anonyme'},
            format='json',
        )

        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
        self.assertFalse(Expertise.objects.exists())

    def test_staff_user_can_create_expertise(self):
        from django.contrib.auth import get_user_model

        staff_user = get_user_model().objects.create_user(
            username='editor', password='test-password-strong', is_staff=True
        )
        self.client.force_authenticate(user=staff_user)

        response = self.client.post(
            '/api/v1/expertises/',
            {'title': 'Expertise autorisée', 'summary': 'Créée par un membre autorisé'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(Expertise.objects.get().title, 'Expertise autorisée')
