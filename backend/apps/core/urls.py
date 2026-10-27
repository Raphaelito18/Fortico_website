"""
Routes de l'application « core » (montées sous /api/v1/).
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.core.views import (
    CompanyProfileView,
    ContactMessageCreateView,
    ContactMessageViewSet,
)

router = DefaultRouter()
router.register(
    r'contact-messages',
    ContactMessageViewSet,
    basename='contactmessage',
)

app_name = 'core'

urlpatterns = [
    path('company/', CompanyProfileView.as_view(), name='company'),
    path('contact/', ContactMessageCreateView.as_view(), name='contact'),
    path('', include(router.urls)),
]
