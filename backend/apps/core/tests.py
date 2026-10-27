from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.core.models import CompanyProfile, ContactMessage


class CompanyProfileApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_company_profile_is_public_and_read_only(self):
        CompanyProfile.objects.create(name='FORTICO Madagascar', slogan='Slogan validé')

        response = self.client.get('/api/v1/company/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'FORTICO Madagascar')
        self.assertEqual(response.data['slogan'], 'Slogan validé')
        self.assertEqual(CompanyProfile.objects.count(), 1)

    def test_company_profile_is_created_when_not_configured(self):
        response = self.client.get('/api/v1/company/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(CompanyProfile.objects.count(), 1)


class ContactMessageApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = '/api/v1/contact/'

    def test_valid_contact_message_is_saved(self):
        response = self.client.post(
            self.url,
            {
                'name': 'Jean Exemple',
                'email': 'jean@example.com',
                'subject': 'Demande de renseignements',
                'message': 'Bonjour, je souhaite obtenir des renseignements.',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ContactMessage.objects.count(), 1)
        message = ContactMessage.objects.get()
        self.assertEqual(message.email, 'jean@example.com')
        self.assertNotIn('email', response.data)

    def test_invalid_contact_message_is_rejected(self):
        response = self.client.post(
            self.url,
            {
                'name': 'J',
                'email': 'adresse-invalide',
                'subject': 'x',
                'message': 'court',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(ContactMessage.objects.count(), 0)

    def test_contact_admin_endpoint_rejects_anonymous_user(self):
        response = self.client.get('/api/v1/contact-messages/')

        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
