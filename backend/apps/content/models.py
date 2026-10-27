"""
Modèles de l'application « content » : expertises, réalisations,
certificats et actualités/publications.
"""

from django.db import models
from django.utils import timezone

from apps.core.models import (
    ImageMixin,
    PublishableModel,
    SluggedModel,
    TimeStampedModel,
)
from apps.core.utils import unique_slugify
from apps.core.storage import PrivateMediaStorage
from apps.core.validators import document_validators


def certificate_document_storage():
    """Stockage privé : les documents se téléchargent via une vue autorisée."""
    return PrivateMediaStorage()


class Category(TimeStampedModel):
    """Catégorie d'actualité ou de publication (ex. : « Chantier », « Partenariat »)."""

    class Meta:
        verbose_name = 'catégorie'
        verbose_name_plural = 'catégories'
        ordering = ['name']

    name = models.CharField('nom', max_length=100, unique=True)
    slug = models.SlugField('identifiant d\'URL', max_length=120, unique=True, blank=True)
    description = models.TextField('description', blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.name)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name


class Expertise(SluggedModel, ImageMixin, PublishableModel, TimeStampedModel):
    """Une expertise ou un service proposé par FORTICO."""

    class Meta:
        verbose_name = 'expertise'
        verbose_name_plural = 'expertises'
        ordering = ['order', 'title']

    title = models.CharField('titre', max_length=200)
    summary = models.CharField(
        'résumé',
        max_length=300,
        help_text='Phrase courte affichée sur les cartes.',
    )
    description = models.TextField('description détaillée', blank=True)
    icon = models.CharField(
        'icône',
        max_length=60,
        blank=True,
        help_text='Nom de l\'icône utilisée (ex. : « wrench »). À valider avec le client.',
    )
    order = models.PositiveSmallIntegerField('ordre d\'affichage', default=0)
    is_featured = models.BooleanField('mise en avant', default=False)

    def __str__(self) -> str:
        return self.title


class GalleryImage(ImageMixin, TimeStampedModel):
    """Image de la galerie d'un projet."""

    class Meta:
        verbose_name = 'image de galerie'
        verbose_name_plural = 'images de galerie'
        ordering = ['order', 'id']

    project = models.ForeignKey(
        'Project',
        related_name='gallery_images',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name='projet',
    )
    caption = models.CharField('légende', max_length=250, blank=True)
    order = models.PositiveSmallIntegerField('ordre d\'affichage', default=0)

    def __str__(self) -> str:
        return self.caption or f'Image #{self.pk}'


class Project(SluggedModel, ImageMixin, PublishableModel, TimeStampedModel):
    """Une réalisation (projet) de FORTICO."""

    class Meta:
        verbose_name = 'réalisation'
        verbose_name_plural = 'réalisations'
        ordering = ['order', '-completed_date']

    title = models.CharField('titre', max_length=200)
    client_name = models.CharField('client', max_length=200, blank=True)
    sector = models.CharField('secteur d\'activité', max_length=150, blank=True)
    location = models.CharField('lieu', max_length=150, blank=True)
    summary = models.CharField('résumé', max_length=300, blank=True)
    description = models.TextField('description', blank=True)
    completed_date = models.DateField('date de réalisation', blank=True, null=True)
    order = models.PositiveSmallIntegerField('ordre d\'affichage', default=0)
    is_featured = models.BooleanField('mise en avant', default=False)

    def __str__(self) -> str:
        return self.title


class Certificate(SluggedModel, ImageMixin, PublishableModel, TimeStampedModel):
    """Un certificat ou une référence professionnelle."""

    class Meta:
        verbose_name = 'certificat'
        verbose_name_plural = 'certificats'
        ordering = ['order', '-issue_date']

    title = models.CharField('titre', max_length=200)
    reference = models.CharField(
        'numéro de référence',
        max_length=100,
        blank=True,
        help_text='Ex. : « CERT-2024-017 ».',
    )
    issuer = models.CharField('organisme émetteur', max_length=200, blank=True)
    description = models.TextField('description', blank=True)
    document = models.FileField(
        'document (PDF)',
        upload_to='certificates/documents/',
        storage=certificate_document_storage(),
        blank=True,
        null=True,
        validators=document_validators(),
    )
    issue_date = models.DateField('date d\'obtention', blank=True, null=True)
    expiry_date = models.DateField('date d\'expiration', blank=True, null=True)
    order = models.PositiveSmallIntegerField('ordre d\'affichage', default=0)

    def __str__(self) -> str:
        return self.title


class Article(SluggedModel, ImageMixin, PublishableModel, TimeStampedModel):
    """Une actualité ou une publication du site."""

    class Meta:
        verbose_name = 'actualité'
        verbose_name_plural = 'actualités'
        ordering = ['-published_date']

    title = models.CharField('titre', max_length=200)
    excerpt = models.TextField(
        'chapô',
        blank=True,
        help_text='Résumé affiché sur la page « Actualités ».',
    )
    content = models.TextField('contenu', blank=True)
    category = models.ForeignKey(
        Category,
        related_name='articles',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name='catégorie',
    )
    author = models.CharField('auteur', max_length=150, blank=True)
    published_date = models.DateField('date de publication', blank=True, null=True)
    is_featured = models.BooleanField('mise en avant', default=False)

    def save(self, *args, **kwargs):
        # Par défaut, la date de publication est la date du jour.
        if not self.published_date:
            self.published_date = timezone.localdate()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.title
