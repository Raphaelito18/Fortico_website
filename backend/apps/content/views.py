"""
Vues de l'application « content ».
"""

from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
import mimetypes

from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView

from apps.content.models import (
    Article,
    Category,
    Certificate,
    Expertise,
    Project,
)
from apps.content.serializers import (
    ArticleDetailSerializer,
    ArticleListSerializer,
    CategorySerializer,
    CertificateSerializer,
    ExpertiseDetailSerializer,
    ExpertiseListSerializer,
    ProjectDetailSerializer,
    ProjectListSerializer,
)
from apps.core.permissions import IsAdminOrReadOnly


class PublishedOnlyMixin:
    """
    Ne renvoie que les contenus « publiés » aux visiteurs anonymes.

    Les administrateurs connectés voient tous les contenus, y compris les
    brouillons, ce qui facilite la relecture avant publication.
    """

    def get_queryset(self):
        queryset = super().get_queryset()
        user = getattr(self.request, 'user', None)
        if not (user and user.is_authenticated and user.is_staff):
            queryset = queryset.filter(is_published=True)
        return queryset


class ExpertiseViewSet(PublishedOnlyMixin, viewsets.ModelViewSet):
    """Expertises et services proposés par FORTICO."""

    permission_classes = [IsAdminOrReadOnly]
    lookup_field = 'slug'
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']
    queryset = Expertise.objects.all()

    def get_serializer_class(self):
        if self.action == 'list':
            return ExpertiseListSerializer
        return ExpertiseDetailSerializer


class ProjectViewSet(PublishedOnlyMixin, viewsets.ModelViewSet):
    """Réalisations et projets de FORTICO."""

    permission_classes = [IsAdminOrReadOnly]
    lookup_field = 'slug'
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']
    queryset = Project.objects.prefetch_related('gallery_images').all()

    def get_serializer_class(self):
        if self.action == 'list':
            return ProjectListSerializer
        return ProjectDetailSerializer


class CertificateViewSet(PublishedOnlyMixin, viewsets.ModelViewSet):
    """Certificats et références professionnelles."""

    permission_classes = [IsAdminOrReadOnly]
    lookup_field = 'slug'
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']
    queryset = Certificate.objects.all()

    def get_serializer_class(self):
        return CertificateSerializer


class ArticleViewSet(PublishedOnlyMixin, viewsets.ModelViewSet):
    """Actualités et publications."""

    permission_classes = [IsAdminOrReadOnly]
    lookup_field = 'slug'
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']
    queryset = Article.objects.select_related('category').all()

    def get_serializer_class(self):
        if self.action == 'list':
            return ArticleListSerializer
        return ArticleDetailSerializer


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """Catégories d'actualités (lecture seule côté public)."""

    permission_classes = [AllowAny]
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = 'slug'


class CertificateDocumentView(APIView):
    """Télécharge un document seulement après contrôle de publication."""

    @extend_schema(responses={200: OpenApiTypes.BINARY})
    def get(self, request, slug):
        certificate = get_object_or_404(Certificate, slug=slug)
        user = request.user
        if not certificate.is_published and not (
            user.is_authenticated and user.is_staff
        ):
            raise Http404
        if not certificate.document:
            raise Http404
        try:
            response = FileResponse(
                certificate.document.open('rb'),
                content_type='application/pdf',
                as_attachment=True,
                filename=f'{certificate.slug}.pdf',
            )
        except (OSError, ValueError) as error:
            raise Http404 from error
        response['X-Content-Type-Options'] = 'nosniff'
        response['Cache-Control'] = 'no-store'
        return response


class ContentImageView(APIView):
    """Sert une image de contenu uniquement si son contenu est publiable."""

    content_models = {
        'expertise': Expertise,
        'project': Project,
        'certificate': Certificate,
        'article': Article,
    }

    def _serve(self, request, instance, published):
        if not instance.image:
            raise Http404
        user = request.user
        if not published and not (user.is_authenticated and user.is_staff):
            raise Http404
        try:
            stream = instance.image.open('rb')
            content_type = mimetypes.guess_type(instance.image.name)[0] or 'application/octet-stream'
            response = FileResponse(stream, content_type=content_type)
        except (OSError, ValueError) as error:
            raise Http404 from error
        response['X-Content-Type-Options'] = 'nosniff'
        response['Cache-Control'] = 'no-store'
        return response

    @extend_schema(responses={200: OpenApiTypes.BINARY})
    def get(self, request, kind, slug):
        model = self.content_models.get(kind)
        if model is None:
            raise Http404
        instance = get_object_or_404(model, slug=slug)
        return self._serve(request, instance, instance.is_published)


class GalleryImageView(ContentImageView):
    @extend_schema(responses={200: OpenApiTypes.BINARY})
    def get(self, request, slug, image_id):
        project = get_object_or_404(Project, slug=slug)
        image = get_object_or_404(project.gallery_images, pk=image_id)
        return self._serve(request, image, project.is_published)
