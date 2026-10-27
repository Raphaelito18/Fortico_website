"""
Vues de l'application « core ».
"""

from django.core.mail import send_mail
from django.conf import settings
import logging
from rest_framework import status, viewsets
from rest_framework.generics import CreateAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from apps.core.models import CompanyProfile, ContactMessage
from apps.core.serializers import (
    CompanyProfileSerializer,
    ContactMessageCreateSerializer,
    ContactMessageSerializer,
)

logger = logging.getLogger(__name__)


class CompanyProfileView(RetrieveAPIView):
    """Informations générales de l'entreprise (lecture seule)."""

    serializer_class = CompanyProfileSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        return CompanyProfile.get_solo()


class ContactMessageCreateView(CreateAPIView):
    """
    Réception des demandes envoyées depuis le formulaire de contact.

    - accessible à tous (c'est un formulaire public) ;
    - limité à 5 envois par heure et par adresse IP (protection anti-abus) ;
    - le message n'est jamais renvoyé tel quel à l'expéditeur, seule la
      confirmation de réception est renvoyée.
    """

    serializer_class = ContactMessageCreateSerializer
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'contact'

    def perform_create(self, serializer):
        request = self.request
        serializer.save(
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:300],
        )
        self._send_notification(serializer.instance)

    @staticmethod
    def _get_client_ip(request):
        proxy_count = settings.REST_FRAMEWORK.get('NUM_PROXIES', 0)
        forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
        chain = [address.strip() for address in forwarded.split(',') if address.strip()]
        if proxy_count and len(chain) >= proxy_count:
            return chain[-proxy_count]
        return request.META.get('REMOTE_ADDR')

    @staticmethod
    def _send_notification(message):
        """Envoie un e-mail de notification à l'équipe FORTICO."""
        recipient = getattr(settings, 'CONTACT_NOTIFICATION_EMAIL', '')
        if not recipient:
            # Aucune adresse configurée : on ne bloque pas la demande.
            return

        body = (
            f'Une nouvelle demande de contact a été reçue.\n\n'
            f'Nom : {message.name}\n'
            f'E-mail : {message.email}\n'
            f'Objet : {message.subject}\n\n'
            f'{message.message}\n'
        )

        try:
            send_mail(
                subject=f'[Site FORTICO] {message.subject}',
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                fail_silently=False,
            )
        except Exception:
            # Une erreur d'envoi ne doit jamais faire échouer la soumission
            # du formulaire : la demande reste enregistrée en base.
            logger.exception('Échec de l’envoi de notification du formulaire de contact.')

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            {
                'message': (
                    'Merci ! Votre message a bien été envoyé. '
                    'Nous vous répondrons dans les meilleurs délais.'
                )
            },
            status=status.HTTP_201_CREATED,
        )


class ContactMessageViewSet(viewsets.ModelViewSet):
    """
    Gestion des demandes de contact (réservée aux administrateurs).
    """

    serializer_class = ContactMessageSerializer
    permission_classes = [IsAdminUser]
    queryset = ContactMessage.objects.all()
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        queryset = super().get_queryset()
        # Filtre simple « ?handled=true|false »
        handled = self.request.query_params.get('handled')
        if handled in {'true', 'false'}:
            queryset = queryset.filter(is_handled=(handled == 'true'))
        return queryset
