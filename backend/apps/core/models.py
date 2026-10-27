"""
Modèles de base réutilisés par les applications « core » et « content ».
"""

from django.db import models

from apps.core.utils import image_upload_path, unique_slugify
from apps.core.storage import PrivateMediaStorage
from apps.core.validators import image_validators


class TimeStampedModel(models.Model):
    """Ajoute automatiquement les dates de création et de modification."""

    created_at = models.DateTimeField('créé le', auto_now_add=True)
    updated_at = models.DateTimeField('modifié le', auto_now=True)

    class Meta:
        abstract = True


class PublishableModel(models.Model):
    """Ajoute la bascule « publié / brouillon »."""

    is_published = models.BooleanField(
        'publié',
        default=False,
        help_text='Décochez pour masquer cet élément du site public.',
    )

    class Meta:
        abstract = True


class SluggedModel(models.Model):
    """
    Ajoute une URL lisible (« slug ») générée automatiquement.

    Le slug peut être renseigné manuellement ; sinon il est calculé à partir
    du titre et rendu unique.
    """

    slug = models.SlugField(
        'identifiant d\'URL',
        max_length=220,
        unique=True,
        blank=True,
        help_text='Laissez vide pour générer automatiquement à partir du titre.',
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.slug and getattr(self, 'title', None):
            self.slug = unique_slugify(self, self.title)
        super().save(*args, **kwargs)


class ImageMixin(models.Model):
    """
    Associe une image et un texte alternatif (accessibilité).

    Le dossier de stockage est calculé automatiquement à partir du modèle
    (« expertises/… », « projects/… », etc.).
    """

    image = models.ImageField(
        'image',
        upload_to=image_upload_path,
        storage=PrivateMediaStorage(),
        blank=True,
        null=True,
        validators=image_validators(),
    )
    alt_text = models.CharField(
        'texte alternatif',
        max_length=200,
        blank=True,
        help_text='Décrit l\'image pour les lecteurs d\'écran et le référencement.',
    )

    class Meta:
        abstract = True


# ---------------------------------------------------------------------------
# Modèles concrets de l'application « core »
# ---------------------------------------------------------------------------
class CompanyProfile(TimeStampedModel):
    """
    Informations générales de l'entreprise (une seule fiche, « singleton »).

    Les valeurs saisies ici alimentent l'en-tête, le pied de page et la page
    « À propos » du site public.
    """

    class Meta:
        verbose_name = 'informations de l\'entreprise'
        verbose_name_plural = 'informations de l\'entreprise'

    # --- Identité ---
    name = models.CharField('nom', max_length=200, default='FORTICO')
    legal_name = models.CharField('raison sociale', max_length=200, blank=True)
    slogan = models.CharField(
        'slogan',
        max_length=250,
        blank=True,
        help_text='Phrase courte affichée sous le nom.',
    )
    short_description = models.TextField(
        'description courte',
        blank=True,
        help_text='Résumé de 2 à 3 phrases, utilisé sur la page d\'accueil.',
    )
    description = models.TextField(
        'présentation détaillée',
        blank=True,
        help_text='Texte complet de la page « À propos de nous ».',
    )
    mission = models.TextField('mission', blank=True)
    values = models.JSONField(
        'valeurs',
        default=list,
        blank=True,
        help_text='Liste de valeurs, une par ligne (ex. : ["Qualité", "Engagement"]).',
    )

    # --- Visuels ---
    logo = models.ImageField(
        'logo', upload_to='entreprise/', blank=True, null=True,
        validators=image_validators(),
    )
    cover_image = models.ImageField(
        'image de couverture',
        upload_to='entreprise/',
        blank=True,
        null=True,
        validators=image_validators(),
    )

    # --- Coordonnées ---
    email = models.EmailField('adresse e-mail', blank=True)
    phone = models.CharField('téléphone', max_length=50, blank=True)
    address = models.CharField('adresse', max_length=250, blank=True)
    city = models.CharField('ville', max_length=100, blank=True)
    postal_code = models.CharField('code postal', max_length=20, blank=True)
    country = models.CharField('pays', max_length=100, default='Madagascar')
    map_url = models.URLField(
        'lien vers la localisation',
        blank=True,
        help_text='Lien Google Maps vers l\'adresse de l\'entreprise.',
    )

    # --- Réseaux sociaux ---
    facebook_url = models.URLField('Facebook', blank=True)
    linkedin_url = models.URLField('LinkedIn', blank=True)
    instagram_url = models.URLField('Instagram', blank=True)
    youtube_url = models.URLField('YouTube', blank=True)

    def save(self, *args, **kwargs):
        """Garantit qu'il n'existe qu'une seule fiche d'informations."""
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Empêche la suppression de la fiche (elle est recréée à la demande)."""
        pass

    @classmethod
    def get_solo(cls) -> 'CompanyProfile':
        """Retourne la fiche d'informations, en la créant si nécessaire."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self) -> str:
        return self.name or 'FORTICO'


class ContactMessage(TimeStampedModel):
    """Demande reçue depuis le formulaire de contact du site public."""

    class Meta:
        verbose_name = 'demande de contact'
        verbose_name_plural = 'demandes de contact'
        ordering = ['-created_at']

    name = models.CharField('nom', max_length=150)
    email = models.EmailField('adresse e-mail')
    subject = models.CharField('objet', max_length=200)
    message = models.TextField('message')

    # --- Suivi ---
    is_handled = models.BooleanField('traité', default=False)
    handled_at = models.DateTimeField('traité le', blank=True, null=True)
    admin_notes = models.TextField(
        'notes internes',
        blank=True,
        help_text='Visible uniquement dans l\'administration.',
    )
    ip_address = models.GenericIPAddressField('adresse IP', blank=True, null=True)
    user_agent = models.CharField('navigateur', max_length=300, blank=True)

    def mark_as_handled(self):
        """Marque la demande comme traitée et horodate le traitement."""
        from django.utils import timezone

        self.is_handled = True
        self.handled_at = timezone.now()
        self.save(update_fields=['is_handled', 'handled_at', 'updated_at'])

    def __str__(self) -> str:
        return f'{self.subject} — {self.name}'
