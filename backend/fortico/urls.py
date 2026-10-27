"""
URLs du projet FORTICO Madagascar.

Organisation :
  /admin/            → administration Django (gestion des contenus)
  /api/v1/           → API REST consumed by the React front-end
  /api/docs/         → documentation interactive de l'API (Swagger UI)
"""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from fortico.seo import robots_txt, sitemap_xml

admin.site.site_header = 'Administration FORTICO'
admin.site.site_title = 'FORTICO Madagascar'
admin.site.index_title = 'Gestion des contenus du site'

urlpatterns = [
    path('robots.txt', robots_txt, name='robots-txt'),
    path('sitemap.xml', sitemap_xml, name='sitemap-xml'),
    # Administration Django
    path('admin/', admin.site.urls),

    # API REST
    path('api/v1/', include('apps.core.urls')),
    path('api/v1/', include('apps.content.urls')),

    # Documentation de l'API
    path('api/schema/', SpectacularAPIView.as_view(), name='api-schema'),
    path(
        'api/docs/',
        SpectacularSwaggerView.as_view(url_name='api-schema'),
        name='api-docs',
    ),

    # Connexion à l'API via l'interface interactive de DRF
    path('api-auth/', include('rest_framework.urls')),
]
