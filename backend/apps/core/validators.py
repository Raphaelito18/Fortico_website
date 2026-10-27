"""
Validateurs partagés (taille et format des fichiers envoyés).

Les fonctions de validation sont définies au niveau du module (et non sous
forme de « lambda ») afin de pouvoir être sérialisées dans les migrations
Django.
"""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.template.defaultfilters import filesizeformat

# Formats d'images acceptés pour les contenus du site.
ALLOWED_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'webp', 'gif', 'avif']

# Formats de documents acceptés (certificats au format PDF).
ALLOWED_DOCUMENT_EXTENSIONS = ['pdf']


def get_max_upload_size_mb() -> int:
    """Taille maximale autorisée (en Mo), lisible dans les réglages."""
    return getattr(settings, 'MAX_UPLOAD_SIZE_MB', 5)


def validate_file_size(file):
    """Refuse un fichier trop volumineux."""
    max_size_mb = get_max_upload_size_mb()
    max_bytes = max_size_mb * 1024 * 1024
    size = getattr(file, 'size', 0)

    if size > max_bytes:
        raise ValidationError(
            f'Le fichier est trop volumineux ({filesizeformat(size)}). '
            f'Taille maximale autorisée : {max_size_mb} Mo.'
        )


def _get_extension(file) -> str:
    name = getattr(file, 'name', '') or ''
    if '.' not in name:
        return ''
    return name.rsplit('.', 1)[-1].lower()


def validate_image_extension(file):
    """Refuse les images qui ne sont pas dans la liste des formats autorisés."""
    extension = _get_extension(file)

    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError(
            'Format d\'image non autorisé. Formats acceptés : '
            + ', '.join(ALLOWED_IMAGE_EXTENSIONS)
            + '.'
        )


def validate_document_extension(file):
    """Refuse les documents qui ne sont pas au format PDF."""
    extension = _get_extension(file)

    if extension not in ALLOWED_DOCUMENT_EXTENSIONS:
        raise ValidationError(
            'Format de document non autorisé. Format accepté : '
            + ', '.join(ALLOWED_DOCUMENT_EXTENSIONS)
            + '.'
        )

    # L'extension seule ne protège pas contre un exécutable renommé en .pdf.
    # UploadedFile peut être consommé ici : repositionner le curseur ensuite.
    position = file.tell() if hasattr(file, 'tell') else 0
    try:
        header = file.read(5)
    finally:
        if hasattr(file, 'seek'):
            file.seek(position)
    if header != b'%PDF-':
        raise ValidationError('Le contenu du fichier n’est pas un document PDF valide.')


def image_validators():
    """Liste de validateurs à appliquer aux champs ImageField."""
    return [validate_image_extension, validate_file_size]


def document_validators():
    """Liste de validateurs à appliquer aux champs FileField."""
    return [validate_document_extension, validate_file_size]
