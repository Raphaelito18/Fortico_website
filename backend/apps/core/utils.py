"""
Utilitaires partagés par les applications du projet.
"""

import re
import unicodedata

from django.utils.text import slugify


def slugify_french(value: str) -> str:
    """
    Transforme un texte en « slug » lisible et compatible avec les URL.

    Exemple : « Réalisations & Projets » -> « realisations-projets »
    """
    # Normalise les caractères accentués : "é" -> "e", "à" -> "a", ...
    normalized = unicodedata.normalize('NFKD', value)
    ascii_value = normalized.encode('ascii', 'ignore').decode('ascii')
    # Retire les caractères qui ne sont ni lettres, ni chiffres, ni tirets.
    cleaned = re.sub(r'[^\w\s-]', '', ascii_value).strip().lower()
    return re.sub(r'[-\s]+', '-', cleaned)


def unique_slugify(model_instance, value: str, slug_field: str = 'slug') -> str:
    """
    Génère un slug unique pour un modèle donné.

    Si un enregistrement possède déjà ce slug, un suffixe numérique est
    ajouté (-2, -3, ...) jusqu'à trouver une valeur libre.
    """
    base = slugify_french(value)[:200] or 'element'
    model_class = model_instance.__class__
    slug = base
    suffix = 2

    while (
        model_class._default_manager.filter(**{slug_field: slug})
        .exclude(pk=model_instance.pk)
        .exists()
    ):
        slug = f'{base}-{suffix}'
        suffix += 1

    return slug


def image_upload_path(instance, filename: str) -> str:
    """
    Dossier de destination d'une image, calculé à partir du modèle.

    Chaque type de contenu dispose ainsi de son propre dossier :
    « expertises/… », « projects/… », « certificates/… », « articles/… ».
    """
    return f'{instance._meta.model_name}/{filename}'
