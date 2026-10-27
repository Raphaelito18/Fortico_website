"""
Administration Django de l'application « core ».
"""

from django.contrib import admin, messages
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from apps.core.models import CompanyProfile, ContactMessage


@admin.register(CompanyProfile)
class CompanyProfileAdmin(admin.ModelAdmin):
    """
    Fiche unique contenant les informations générales de l'entreprise.

    L'utilisateur ne peut pas créer une seconde fiche ni la supprimer :
    le site en utilise toujours exactement une.
    """

    fieldsets = (
        ('Identité', {
            'fields': ('name', 'legal_name', 'slogan', 'short_description'),
        }),
        ('Présentation', {
            'fields': ('description', 'mission', 'values'),
        }),
        ('Visuels', {
            'fields': ('logo', 'cover_image'),
        }),
        ('Coordonnées', {
            'fields': ('email', 'phone', 'address', 'city', 'postal_code', 'country', 'map_url'),
        }),
        ('Réseaux sociaux', {
            'fields': ('facebook_url', 'linkedin_url', 'instagram_url', 'youtube_url'),
            'classes': ('collapse',),
        }),
    )

    readonly_fields = ('updated_at', 'logo_preview', 'cover_preview')

    def has_add_permission(self, request):
        """Une seule fiche est autorisée."""
        return not CompanyProfile.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description='Aperçu du logo')
    def logo_preview(self, obj):
        if obj and obj.logo:
            return mark_safe(
                f'<img src="{obj.logo.url}" alt="logo" style="max-height:90px;" />'
            )
        return '—'

    @admin.display(description='Aperçu de la couverture')
    def cover_preview(self, obj):
        if obj and obj.cover_image:
            return mark_safe(
                f'<img src="{obj.cover_image.url}" alt="couverture" '
                'style="max-height:160px; max-width:320px; object-fit:cover;" />'
            )
        return '—'

    def save_model(self, request, obj, form, change):
        # Le modèle force déjà pk=1 : garantit une fiche unique.
        super().save_model(request, obj, form, change)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    """Gestion des demandes reçues via le formulaire de contact."""

    list_display = (
        'subject',
        'name',
        'email',
        'status_badge',
        'created_at',
    )
    list_filter = ('is_handled', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    readonly_fields = ('created_at', 'updated_at', 'ip_address', 'user_agent', 'handled_at')
    date_hierarchy = 'created_at'
    list_per_page = 25
    actions = ('mark_as_handled', 'mark_as_unhandled')

    fieldsets = (
        ('Message', {
            'fields': ('name', 'email', 'subject', 'message'),
        }),
        ('Suivi', {
            'fields': ('is_handled', 'handled_at', 'admin_notes'),
            'classes': ('collapse',),
        }),
        ('Informations techniques', {
            'fields': ('ip_address', 'user_agent', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Statut', ordering='is_handled')
    def status_badge(self, obj):
        if obj.is_handled:
            return format_html(
                '<span style="background:#e6f4ea;color:#137333;padding:3px 10px;'
                'border-radius:12px;font-size:12px;">Traitée</span>'
            )
        return format_html(
            '<span style="background:#fef7e0;color:#b06000;padding:3px 10px;'
            'border-radius:12px;font-size:12px;">À traiter</span>'
        )

    @admin.action(description='Marquer comme traitée(s)')
    def mark_as_handled(self, request, queryset):
        updated = 0
        for message in queryset.filter(is_handled=False):
            message.mark_as_handled()
            updated += 1
        self.message_user(
            request,
            f'{updated} demande(s) marquée(s) comme traitée(s).',
            messages.SUCCESS,
        )

    @admin.action(description='Marquer comme non traitée(s)')
    def mark_as_unhandled(self, request, queryset):
        updated = queryset.filter(is_handled=True).update(
            is_handled=False, handled_at=None
        )
        self.message_user(
            request,
            f'{updated} demande(s) replacée(s) dans « à traiter ».',
            messages.SUCCESS,
        )
