"""
Administration Django de l'application « content ».
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from apps.content.models import (
    Article,
    Category,
    Certificate,
    Expertise,
    GalleryImage,
    Project,
)


class GalleryImageInline(admin.TabularInline):
    """Galerie d'images d'un projet, modifiable directement depuis la fiche."""

    model = GalleryImage
    extra = 1
    fields = ('image', 'alt_text', 'caption', 'order')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'article_count')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

    @admin.display(description='nombre d\'articles')
    def article_count(self, obj):
        return obj.articles.count()


@admin.register(Expertise)
class ExpertiseAdmin(admin.ModelAdmin):
    list_display = ('title', 'summary_short', 'order', 'is_featured', 'is_published')
    list_editable = ('order', 'is_featured', 'is_published')
    list_filter = ('is_published', 'is_featured')
    search_fields = ('title', 'summary', 'description')
    prepopulated_fields = {'slug': ('title',)}
    ordering = ('order', 'title')

    fieldsets = (
        ('Contenu', {
            'fields': ('title', 'slug', 'summary', 'description'),
        }),
        ('Visuels', {
            'fields': ('icon', 'image', 'alt_text'),
        }),
        ('Affichage', {
            'fields': ('order', 'is_featured', 'is_published'),
        }),
    )

    @admin.display(description='résumé')
    def summary_short(self, obj):
        return (obj.summary[:60] + '…') if len(obj.summary) > 60 else obj.summary


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'client_name', 'sector', 'location', 'completed_date',
                    'is_featured', 'is_published')
    list_editable = ('is_featured', 'is_published')
    list_filter = ('is_published', 'is_featured', 'sector')
    search_fields = ('title', 'client_name', 'summary', 'description')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [GalleryImageInline]
    date_hierarchy = 'completed_date'
    ordering = ('order', '-completed_date')

    fieldsets = (
        ('Contenu', {
            'fields': ('title', 'slug', 'client_name', 'sector', 'location',
                       'summary', 'description'),
        }),
        ('Visuels', {
            'fields': ('image', 'alt_text'),
        }),
        ('Informations', {
            'fields': ('completed_date', 'order', 'is_featured', 'is_published'),
        }),
    )


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('title', 'reference', 'issuer', 'issue_date', 'expiry_date',
                    'is_published')
    list_editable = ('is_published',)
    list_filter = ('is_published', 'issuer')
    search_fields = ('title', 'reference', 'issuer', 'description')
    prepopulated_fields = {'slug': ('title',)}
    ordering = ('order', '-issue_date')

    fieldsets = (
        ('Contenu', {
            'fields': ('title', 'slug', 'reference', 'issuer', 'description'),
        }),
        ('Fichiers', {
            'fields': ('image', 'alt_text', 'document'),
        }),
        ('Validité et affichage', {
            'fields': ('issue_date', 'expiry_date', 'order', 'is_published'),
        }),
    )

    @admin.display(description='visuel')
    def image_preview(self, obj):
        if obj and obj.image:
            return mark_safe(
                f'<img src="{obj.image.url}" alt="{obj.alt_text}" '
                'style="max-height:120px; max-width:180px; object-fit:cover;" />'
            )
        return '—'


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'author', 'published_date', 'is_featured',
                    'is_published')
    list_editable = ('is_featured', 'is_published')
    list_filter = ('is_published', 'is_featured', 'category')
    search_fields = ('title', 'excerpt', 'content', 'author')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'published_date'
    ordering = ('-published_date',)

    fieldsets = (
        ('Contenu', {
            'fields': ('title', 'slug', 'excerpt', 'content'),
        }),
        ('Visuels', {
            'fields': ('image', 'alt_text'),
        }),
        ('Publication', {
            'fields': ('category', 'author', 'published_date', 'is_featured', 'is_published'),
        }),
    )
