"""
Routes de l'application « content » (montées sous /api/v1/).
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.content.views import (
    ArticleViewSet,
    CategoryViewSet,
    CertificateViewSet,
    CertificateDocumentView,
    ContentImageView,
    GalleryImageView,
    ExpertiseViewSet,
    ProjectViewSet,
)

router = DefaultRouter()
router.register(r'expertises', ExpertiseViewSet, basename='expertise')
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'certificates', CertificateViewSet, basename='certificate')
router.register(r'articles', ArticleViewSet, basename='article')
router.register(r'categories', CategoryViewSet, basename='category')

app_name = 'content'

urlpatterns = [
    path('certificates/<slug:slug>/document/', CertificateDocumentView.as_view(), name='certificate-document'),
    path('<str:kind>/<slug:slug>/image/', ContentImageView.as_view(), name='content-image'),
    path('projects/<slug:slug>/images/<int:image_id>/', GalleryImageView.as_view(), name='gallery-image'),
    path('', include(router.urls)),
]
