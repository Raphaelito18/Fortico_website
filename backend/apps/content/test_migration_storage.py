from importlib import import_module
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase


class MemoryStorage:
    def __init__(self, files=None):
        self.files = dict(files or {})

    def exists(self, name):
        return name in self.files

    def open(self, name, mode):
        return BytesIO(self.files[name])

    def save(self, name, content):
        content.seek(0)
        self.files[name] = content.read()
        return name


class Manager:
    def __init__(self, rows):
        self.rows = rows

    def exclude(self, **kwargs):
        return self

    def iterator(self):
        return iter(self.rows)


class ExistingContentFileMigrationTests(SimpleTestCase):
    def test_existing_file_names_and_references_are_copied_without_deleting_originals(self):
        migration = import_module('apps.content.migrations.0002_alter_article_is_published_and_more')
        original_names = {
            'article.jpg': b'article bytes',
            'certificate.png': b'image bytes',
            'certificate.pdf': b'%PDF-1.4 certificate',
            'expertise.webp': b'expertise bytes',
            'galleryimage.jpg': b'gallery bytes',
            'project.jpg': b'project bytes',
        }
        public_storage = MemoryStorage(original_names)
        private_storage = MemoryStorage()
        names_by_model = {
            'Article': {'image': 'article.jpg'},
            'Certificate': {'image': 'certificate.png', 'document': 'certificate.pdf'},
            'Expertise': {'image': 'expertise.webp'},
            'GalleryImage': {'image': 'galleryimage.jpg'},
            'Project': {'image': 'project.jpg'},
        }

        class HistoricalApps:
            def get_model(self, app_label, model_name):
                names = names_by_model[model_name]
                row = SimpleNamespace(**{
                    field_name: SimpleNamespace(name=name)
                    for field_name, name in names.items()
                })
                return SimpleNamespace(objects=Manager([row]))

        with (
            patch.object(migration, 'FileSystemStorage', return_value=public_storage),
            patch.object(migration, 'PrivateMediaStorage', return_value=private_storage),
        ):
            migration.copy_existing_content_files_to_private_storage(HistoricalApps(), None)

        self.assertEqual(private_storage.files, original_names)
        self.assertEqual(public_storage.files, original_names)
        self.assertEqual(names_by_model['Certificate']['document'], 'certificate.pdf')
