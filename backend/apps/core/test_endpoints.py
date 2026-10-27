from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.content.models import Article, Category, Certificate, Expertise, Project
from apps.core.models import CompanyProfile, ContactMessage


class CoreEndpointCoverageTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()

    def test_company_profile_is_public_read_only(self):
        CompanyProfile.objects.create(name='Nom à confirmer')
        self.assertEqual(self.client.get('/api/v1/company/').status_code, 200)
        for method in ('post', 'patch', 'delete'):
            response = getattr(self.client, method)('/api/v1/company/', {'name': 'Injection'}, format='json')
            self.assertIn(response.status_code, (401, 403, 405))
        self.assertEqual(CompanyProfile.objects.get().name, 'Nom à confirmer')

    def test_company_public_images_apply_extension_and_size_validators(self):
        with self.assertRaises(ValidationError):
            CompanyProfile._meta.get_field('logo').run_validators(
                SimpleUploadedFile('logo.svg', b'<svg/>')
            )

    def test_category_endpoint_is_read_only(self):
        Category.objects.create(name='Actualité')
        self.assertEqual(self.client.get('/api/v1/categories/').status_code, 200)
        self.assertEqual(self.client.post('/api/v1/categories/', {'name': 'Nouvelle'}, format='json').status_code, 405)

    def test_contact_message_is_validated_saved_and_not_echoed(self):
        valid = {'name': 'Jean Exemple', 'email': 'jean@example.com', 'subject': 'Demande valide', 'message': 'Bonjour, ceci est un message valide.'}
        response = self.client.post('/api/v1/contact/', valid, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(ContactMessage.objects.count(), 1)
        self.assertNotIn('email', response.data)
        invalid = {**valid, 'email': 'pas-une-adresse'}
        self.assertEqual(self.client.post('/api/v1/contact/', invalid, format='json').status_code, 400)
        self.assertEqual(ContactMessage.objects.count(), 1)

    def test_contact_ip_ignores_untrusted_forwarded_for_by_default(self):
        response = self.client.post(
            '/api/v1/contact/',
            {
                'name': 'Jean Exemple',
                'email': 'jean@example.com',
                'subject': 'Demande de renseignements',
                'message': 'Bonjour, je souhaite obtenir des renseignements.',
            },
            format='json',
            REMOTE_ADDR='203.0.113.25',
            HTTP_X_FORWARDED_FOR='198.51.100.99',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ContactMessage.objects.get().ip_address, '203.0.113.25')

    @override_settings(CONTACT_NOTIFICATION_EMAIL='team@example.com', EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_contact_notification_is_created_by_test_mail_backend(self):
        response = self.client.post('/api/v1/contact/', {
            'name': 'Amina Exemple', 'email': 'amina@example.com',
            'subject': 'Contact', 'message': 'Je souhaite vous contacter.',
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['team@example.com'])

    @override_settings(REST_FRAMEWORK={
        'DEFAULT_AUTHENTICATION_CLASSES': [
            'rest_framework.authentication.TokenAuthentication',
            'rest_framework.authentication.SessionAuthentication',
        ],
        'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticatedOrReadOnly'],
        'DEFAULT_RENDERER_CLASSES': [
            'rest_framework.renderers.JSONRenderer',
            'rest_framework.renderers.BrowsableAPIRenderer',
        ],
        'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
        'PAGE_SIZE': 12,
        'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
        'DEFAULT_THROTTLE_RATES': {'anon': '60/hour', 'user': '600/hour', 'contact': '5/hour'},
        'DATETIME_FORMAT': '%d/%m/%Y à %H:%M',
    })
    def test_contact_rate_limit_returns_429(self):
        payload = {'name': 'Amina', 'email': 'amina@example.com', 'subject': 'Bonjour', 'message': 'Un message de contact.'}
        for _ in range(5):
            self.assertEqual(self.client.post('/api/v1/contact/', payload, format='json').status_code, 201)
        self.assertEqual(self.client.post('/api/v1/contact/', payload, format='json').status_code, 429)

    @override_settings(CONTACT_NOTIFICATION_EMAIL='team@example.com')
    def test_mail_failure_is_logged_and_does_not_fail_submission(self):
        with patch('apps.core.views.send_mail', side_effect=OSError('SMTP indisponible')):
            with self.assertLogs('apps.core.views', level='ERROR') as logs:
                response = self.client.post('/api/v1/contact/', {
                    'name': 'Amina Exemple', 'email': 'amina@example.com',
                    'subject': 'Contact', 'message': 'Je souhaite vous contacter.',
                }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(ContactMessage.objects.count(), 1)
        self.assertIn('Échec de l’envoi', logs.output[0])

    def test_contact_admin_crud_is_staff_only(self):
        record = ContactMessage.objects.create(name='Test', email='test@example.com', subject='Test', message='Message enregistré')
        url = f'/api/v1/contact-messages/{record.pk}/'
        self.assertIn(self.client.get('/api/v1/contact-messages/').status_code, (401, 403))
        staff = get_user_model().objects.create_user(username='manager', is_staff=True)
        self.client.force_authenticate(staff)
        listing = self.client.get('/api/v1/contact-messages/?handled=false')
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(listing.data['count'], 1)
        self.assertEqual(self.client.patch(url, {'admin_notes': 'À traiter'}, format='json').status_code, 200)
        self.assertEqual(self.client.delete(url).status_code, 204)

    @override_settings(STORAGES={
        'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
        'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
    })
    def test_django_admin_changelists_for_existing_modules(self):
        admin_user = get_user_model().objects.create_superuser(username='admin', email='admin@example.com', password='test-password')
        from django.test import Client
        browser = Client()
        browser.force_login(admin_user)
        models = (CompanyProfile, Expertise, Project, Certificate, Article, Category, ContactMessage)
        for model in models:
            with self.subTest(model=model.__name__):
                response = browser.get(reverse(f'admin:{model._meta.app_label}_{model._meta.model_name}_changelist'))
                self.assertEqual(response.status_code, 200)
