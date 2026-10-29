from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from fortico.settings import postgres_database_from_url


class PostgresDatabaseUrlTests(SimpleTestCase):
    def test_parses_render_url_and_preserves_ssl_options(self):
        database = postgres_database_from_url(
            'postgresql://fortico%40preview:p%40ss%3Fword@db.example:5433/fortico_preview?sslmode=require',
            conn_max_age=12,
        )

        self.assertEqual(database['ENGINE'], 'django.db.backends.postgresql')
        self.assertEqual(database['NAME'], 'fortico_preview')
        self.assertEqual(database['USER'], 'fortico@preview')
        self.assertEqual(database['PASSWORD'], 'p@ss?word')
        self.assertEqual(database['HOST'], 'db.example')
        self.assertEqual(database['PORT'], '5433')
        self.assertEqual(database['OPTIONS'], {'sslmode': 'require'})
        self.assertEqual(database['CONN_MAX_AGE'], 12)

    def test_rejects_non_postgresql_or_incomplete_urls(self):
        for url in (
            'sqlite:///fortico.db',
            'postgresql://user:password@db.example/',
            'postgresql://user@db.example/fortico',
            'postgresql://user:password/fortico',
        ):
            with self.subTest(url=url):
                with self.assertRaises(ImproperlyConfigured):
                    postgres_database_from_url(url)

    def test_does_not_include_credentials_in_parse_errors(self):
        with self.assertRaises(ImproperlyConfigured) as error:
            postgres_database_from_url('postgresql://private-user:private-password@db.example/')

        self.assertNotIn('private-password', str(error.exception))
