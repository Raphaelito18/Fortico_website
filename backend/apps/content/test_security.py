from django.contrib.auth import get_user_model
from django.core.files.storage import InMemoryStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.test import TransactionTestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from apps.content.models import Article, Certificate, Expertise, Project
from apps.core.validators import validate_file_size, validate_image_extension


class ContentApiCoverageTests(TransactionTestCase):
    def setUp(self):
        self.client = APIClient()

    def test_new_content_is_draft_and_all_public_endpoints_hide_drafts(self):
        cases = (
            (Expertise, 'expertises', {'title': 'Expertise', 'summary': 'Résumé'}),
            (Project, 'projects', {'title': 'Projet'}),
            (Certificate, 'certificates', {'title': 'Certificat'}),
            (Article, 'articles', {'title': 'Actualité'}),
        )
        for model, endpoint, values in cases:
            with self.subTest(model=model.__name__):
                draft = model.objects.create(**values)
                self.assertFalse(draft.is_published)
                url = f'/api/v1/{endpoint}/'
                self.assertEqual(self.client.get(url).data['results'], [])
                self.assertEqual(self.client.get(f'{url}{draft.slug}/').status_code, 404)
                public = model.objects.create(is_published=True, **{**values, 'title': f'{values["title"]} visible'})
                self.assertEqual(len(self.client.get(url).data['results']), 1)
                self.assertEqual(self.client.get(f'{url}{public.slug}/').status_code, 200)

    def test_staff_can_create_update_delete_and_non_staff_cannot_write(self):
        visitor = get_user_model().objects.create_user(username='visitor', password='secret')
        self.client.force_authenticate(visitor)
        denied = self.client.post('/api/v1/projects/', {'title': 'No'}, format='json')
        self.assertEqual(denied.status_code, 403)

        staff = get_user_model().objects.create_user(username='editor', is_staff=True)
        self.client.force_authenticate(staff)
        created = self.client.post('/api/v1/projects/', {'title': 'Projet API'}, format='json')
        self.assertEqual(created.status_code, 201, created.data)
        self.assertFalse(Project.objects.get(slug=created.data['slug']).is_published)
        detail = f'/api/v1/projects/{created.data["slug"]}/'
        self.assertEqual(self.client.patch(detail, {'title': ''}, format='json').status_code, 400)
        self.assertEqual(self.client.patch(detail, {'title': 'Projet modifié'}, format='json').status_code, 200)
        self.assertEqual(self.client.delete(detail).status_code, 204)

        for endpoint, model, payload in (
            ('expertises', Expertise, {'title': 'Expertise API', 'summary': 'Résumé'}),
            ('certificates', Certificate, {'title': 'Certificat API'}),
            ('articles', Article, {'title': 'Actualité API'}),
        ):
            with self.subTest(endpoint=endpoint):
                created = self.client.post(f'/api/v1/{endpoint}/', payload, format='json')
                self.assertEqual(created.status_code, 201, created.data)
                item = model.objects.get(slug=created.data['slug'])
                self.assertFalse(item.is_published)
                detail = f'/api/v1/{endpoint}/{item.slug}/'
                self.assertEqual(self.client.patch(detail, {'title': f'{payload["title"]} modifié'}, format='json').status_code, 200)
                self.assertEqual(self.client.delete(detail).status_code, 204)

    def test_certificate_document_download_obeys_publication(self):
        field = Certificate._meta.get_field('document')
        original_storage = field.storage
        field.storage = InMemoryStorage()
        try:
            certificate = Certificate.objects.create(title='Document à valider')
            certificate.document.save('certificate.pdf', SimpleUploadedFile('certificate.pdf', b'%PDF-1.4\ncontenu'), save=True)
            url = reverse('content:certificate-document', kwargs={'slug': certificate.slug})
            self.assertEqual(self.client.get(url).status_code, 404)
            self.client.force_authenticate(get_user_model().objects.create_user(username='not-staff'))
            self.assertEqual(self.client.get(url).status_code, 404)
            self.client.force_authenticate(user=None)
            self.assertEqual(self.client.get(f'/media/{certificate.document.name}').status_code, 404)

            staff = get_user_model().objects.create_user(username='reviewer', is_staff=True)
            self.client.force_authenticate(staff)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response['Content-Type'], 'application/pdf')
            self.assertEqual(response['Cache-Control'], 'no-store')
            self.assertEqual(b''.join(response.streaming_content), b'%PDF-1.4\ncontenu')
            response.close()

            self.client.force_authenticate(user=None)
            certificate.is_published = True
            certificate.save(update_fields=['is_published'])
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response['Cache-Control'], 'no-store')
            response.close()

            missing = Certificate.objects.create(
                title='Fichier absent',
                is_published=True,
                document='certificates/documents/missing.pdf',
            )
            missing_url = reverse('content:certificate-document', kwargs={'slug': missing.slug})
            self.assertEqual(self.client.get(missing_url).status_code, 404)
        finally:
            field.storage = original_storage

    def test_content_images_are_served_only_for_published_content(self):
        field = Expertise._meta.get_field('image')
        original_storage = field.storage
        field.storage = InMemoryStorage()
        try:
            draft = Expertise.objects.create(title='Image à valider', summary='Brouillon')
            draft.image.save('preview.png', SimpleUploadedFile('preview.png', b'temporary image bytes'), save=True)
            url = reverse('content:content-image', kwargs={'kind': 'expertise', 'slug': draft.slug})
            self.assertEqual(self.client.get(url).status_code, 404)

            staff = get_user_model().objects.create_user(username='image-reviewer', is_staff=True)
            self.client.force_authenticate(staff)
            self.assertEqual(self.client.get(url).status_code, 200)
            self.client.force_authenticate(user=None)

            draft.is_published = True
            draft.save(update_fields=['is_published'])
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            response.close()
            listed = self.client.get('/api/v1/expertises/').data['results'][0]
            self.assertEqual(listed['image'], url)
        finally:
            field.storage = original_storage

    def test_certificate_upload_checks_pdf_signature(self):
        staff = get_user_model().objects.create_user(username='uploader', is_staff=True)
        self.client.force_authenticate(staff)
        response = self.client.post(
            '/api/v1/certificates/',
            {'title': 'Faux PDF', 'document': SimpleUploadedFile('renomme.pdf', b'MZ executable')},
            format='multipart',
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Certificate.objects.exists())

    def test_staff_can_upload_valid_pdf_to_private_storage(self):
        field = Certificate._meta.get_field('document')
        original_storage = field.storage
        field.storage = InMemoryStorage()
        try:
            staff = get_user_model().objects.create_user(username='pdf-uploader', is_staff=True)
            self.client.force_authenticate(staff)
            response = self.client.post(
                '/api/v1/certificates/',
                {'title': 'Document privé', 'document': SimpleUploadedFile('certificate.pdf', b'%PDF-1.4\ncontenu')},
                format='multipart',
            )
            self.assertEqual(response.status_code, 201, response.data)
            self.assertEqual(response.data['document'], reverse('content:certificate-document', kwargs={'slug': response.data['slug']}))
            self.assertTrue(Certificate.objects.get(slug=response.data['slug']).document.storage.exists(
                Certificate.objects.get(slug=response.data['slug']).document.name
            ))
        finally:
            field.storage = original_storage

    def test_image_upload_rejects_invalid_content_and_extension(self):
        staff = get_user_model().objects.create_user(username='image-uploader', is_staff=True)
        self.client.force_authenticate(staff)
        response = self.client.post(
            '/api/v1/expertises/',
            {'title': 'Image invalide', 'summary': 'Contenu incorrect', 'image': SimpleUploadedFile('renamed.png', b'not an image')},
            format='multipart',
        )
        self.assertEqual(response.status_code, 400)
        with self.assertRaises(ValidationError):
            validate_image_extension(SimpleUploadedFile('image.svg', b'<svg/>'))

    @override_settings(MAX_UPLOAD_SIZE_MB=1)
    def test_upload_size_limit_is_enforced(self):
        too_large = SimpleUploadedFile('oversize.pdf', b'x' * (1024 * 1024 + 1))
        with self.assertRaises(ValidationError):
            validate_file_size(too_large)
