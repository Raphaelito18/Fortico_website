"""
Serializers de l'application « content ».
"""

from rest_framework import serializers
from django.urls import reverse
from django.core.exceptions import ValidationError as DjangoValidationError

from apps.content.models import (
    Article,
    Category,
    Certificate,
    Expertise,
    GalleryImage,
    Project,
)


class ProtectedImageModelSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        self._protected_instance = instance
        return super().to_representation(instance)

    def validate_image(self, value):
        try:
            self.Meta.model._meta.get_field('image').run_validators(value)
        except DjangoValidationError as error:
            raise serializers.ValidationError(error.messages) from error
        return value


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description']


class ProtectedImageField(serializers.ImageField):
    """Sérialise les images vers la route qui vérifie la publication."""

    def to_representation(self, value):
        if not value:
            return None
        instance = self.parent._protected_instance
        if instance._meta.model_name == 'galleryimage':
            if not instance.project_id:
                return None
            return reverse('content:gallery-image', kwargs={
                'slug': instance.project.slug,
                'image_id': instance.pk,
            })
        return reverse('content:content-image', kwargs={
            'kind': instance._meta.model_name,
            'slug': instance.slug,
        })


class GalleryImageSerializer(ProtectedImageModelSerializer):
    image = ProtectedImageField(required=False, allow_null=True)

    class Meta:
        model = GalleryImage
        fields = ['id', 'image', 'alt_text', 'caption', 'order']


class ExpertiseListSerializer(ProtectedImageModelSerializer):
    image = ProtectedImageField(required=False, allow_null=True)
    """Version allégée utilisée pour les listes d'expertises."""

    class Meta:
        model = Expertise
        fields = [
            'id',
            'title',
            'slug',
            'summary',
            'icon',
            'image',
            'alt_text',
            'order',
            'is_featured',
        ]

class ExpertiseDetailSerializer(ProtectedImageModelSerializer):
    image = ProtectedImageField(required=False, allow_null=True)
    class Meta:
        model = Expertise
        fields = [
            'id',
            'title',
            'slug',
            'summary',
            'description',
            'icon',
            'image',
            'alt_text',
            'order',
            'is_featured',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProjectListSerializer(ProtectedImageModelSerializer):
    image = ProtectedImageField(required=False, allow_null=True)
    """Version allégée utilisée pour la liste des réalisations."""

    class Meta:
        model = Project
        fields = [
            'id',
            'title',
            'slug',
            'client_name',
            'sector',
            'location',
            'summary',
            'image',
            'alt_text',
            'completed_date',
            'is_featured',
        ]


class ProjectDetailSerializer(ProtectedImageModelSerializer):
    image = ProtectedImageField(required=False, allow_null=True)
    images = GalleryImageSerializer(source='gallery_images', many=True, read_only=True)

    class Meta:
        model = Project
        fields = [
            'id',
            'title',
            'slug',
            'client_name',
            'sector',
            'location',
            'summary',
            'description',
            'image',
            'alt_text',
            'images',
            'completed_date',
            'is_featured',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CertificateSerializer(ProtectedImageModelSerializer):
    image = ProtectedImageField(required=False, allow_null=True)
    document = serializers.FileField(required=False, allow_null=True)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['document'] = (
            reverse('content:certificate-document', kwargs={'slug': instance.slug})
            if instance.document else None
        )
        return data

    def validate_document(self, value):
        try:
            Certificate._meta.get_field('document').run_validators(value)
        except DjangoValidationError as error:
            raise serializers.ValidationError(error.messages) from error
        return value

    class Meta:
        model = Certificate
        fields = [
            'id',
            'title',
            'slug',
            'reference',
            'issuer',
            'description',
            'image',
            'alt_text',
            'document',
            'issue_date',
            'expiry_date',
            'order',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ArticleListSerializer(ProtectedImageModelSerializer):
    image = ProtectedImageField(required=False, allow_null=True)
    """Version allégée utilisée pour la liste des actualités."""

    category = serializers.CharField(source='category.name', read_only=True, default=None)

    class Meta:
        model = Article
        fields = [
            'id',
            'title',
            'slug',
            'excerpt',
            'image',
            'alt_text',
            'category',
            'author',
            'published_date',
            'is_featured',
        ]


class ArticleDetailSerializer(ProtectedImageModelSerializer):
    image = ProtectedImageField(required=False, allow_null=True)
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Article
        fields = [
            'id',
            'title',
            'slug',
            'excerpt',
            'content',
            'image',
            'alt_text',
            'category',
            'author',
            'published_date',
            'is_featured',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
