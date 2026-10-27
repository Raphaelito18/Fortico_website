from django.test import TestCase, override_settings

from apps.content.models import Article, Project


class PublicCrawlerFileTests(TestCase):
    def test_unknown_detail_slugs_return_not_found(self):
        for url in (
            '/api/v1/projects/inconnu/',
            '/api/v1/articles/inconnu/',
        ):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 404)

    @override_settings(PUBLIC_SITE_URL='')
    def test_sitemap_is_not_generated_without_confirmed_public_origin(self):
        response = self.client.get('/sitemap.xml')
        self.assertEqual(response.status_code, 503)

    @override_settings(PUBLIC_SITE_URL='')
    def test_robots_does_not_publish_a_placeholder_sitemap_url(self):
        response = self.client.get('/robots.txt')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('Sitemap:', response.content.decode())

    @override_settings(PUBLIC_SITE_URL='https://fortico.example')
    def test_sitemap_contains_public_routes_and_only_published_detail_slugs(self):
        Project.objects.create(title='Visible project', slug='visible-project', is_published=True)
        Project.objects.create(title='Draft project', slug='draft-project', is_published=False)
        Article.objects.create(title='Visible article', slug='visible-article', is_published=True)
        Article.objects.create(title='Draft article', slug='draft-article', is_published=False)

        response = self.client.get('/sitemap.xml')
        body = response.content.decode()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'].split(';')[0], 'application/xml')
        self.assertIn('https://fortico.example/realisations/visible-project', body)
        self.assertIn('https://fortico.example/actualites/visible-article', body)
        self.assertNotIn('draft-project', body)
        self.assertNotIn('draft-article', body)
        self.assertIn('https://fortico.example/contact/', body)

    @override_settings(PUBLIC_SITE_URL='https://fortico.example')
    def test_robots_references_the_configured_sitemap(self):
        response = self.client.get('/robots.txt')
        self.assertIn('Sitemap: https://fortico.example/sitemap.xml', response.content.decode())
