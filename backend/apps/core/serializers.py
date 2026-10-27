"""
Serializers de l'application « core ».
"""

from rest_framework import serializers

from apps.core.models import CompanyProfile, ContactMessage


class CompanyProfileSerializer(serializers.ModelSerializer):
    """Représentation publique des informations générales de l'entreprise."""

    class Meta:
        model = CompanyProfile
        fields = [
            'name',
            'legal_name',
            'slogan',
            'short_description',
            'description',
            'mission',
            'values',
            'logo',
            'cover_image',
            'email',
            'phone',
            'address',
            'city',
            'postal_code',
            'country',
            'map_url',
            'facebook_url',
            'linkedin_url',
            'instagram_url',
            'youtube_url',
            'updated_at',
        ]
        read_only_fields = fields


class ContactMessageCreateSerializer(serializers.ModelSerializer):
    """
    Serializer utilisé par le formulaire de contact du site public.

    Seuls les champs utiles au visiteur sont acceptés : ni l'adresse IP
    ni les notes internes ne peuvent être renseignés par le client.
    """

    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']

    # Validation côté serveur (en plus de la validation côté navigateur).
    name = serializers.CharField(max_length=150, min_length=2)
    email = serializers.EmailField(max_length=254)
    subject = serializers.CharField(max_length=200, min_length=3)
    message = serializers.CharField(min_length=10)


class ContactMessageSerializer(serializers.ModelSerializer):
    """Serializer complet, réservé à l'administration."""

    class Meta:
        model = ContactMessage
        fields = [
            'id',
            'name',
            'email',
            'subject',
            'message',
            'is_handled',
            'handled_at',
            'admin_notes',
            'ip_address',
            'user_agent',
            'created_at',
        ]
        read_only_fields = ['id', 'ip_address', 'user_agent', 'created_at']
