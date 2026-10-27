"""Public crawler files; the official public origin must be configured explicitly."""

from urllib.parse import urlsplit
from xml.etree.ElementTree import Element, SubElement, tostring

from django.conf import settings
from django.http import HttpResponse
from apps.content.models import Article, Project


def _public_origin():
    value = settings.PUBLIC_SITE_URL.rstrip('/')
    parsed = urlsplit(value)
    if parsed.scheme not in {'https', 'http'} or not parsed.netloc or parsed.path not in {'', '/'}:
        return None
    return value


def robots_txt(request):
    lines = ['User-agent: *']
    if not settings.SEARCH_INDEXING_ENABLED:
        lines.append('Disallow: /')
        return HttpResponse('\n'.join(lines) + '\n', content_type='text/plain; charset=utf-8')

    lines.extend(['Allow: /', 'Disallow: /admin/', 'Disallow: /api/'])
    origin = _public_origin()
    if origin:
        lines.append(f'Sitemap: {origin}/sitemap.xml')
    return HttpResponse('\n'.join(lines) + '\n', content_type='text/plain; charset=utf-8')


def sitemap_xml(request):
    if not settings.SEARCH_INDEXING_ENABLED:
        return HttpResponse('Search indexing is disabled.\n', status=503, content_type='text/plain; charset=utf-8')

    origin = _public_origin()
    if not origin:
        return HttpResponse('PUBLIC_SITE_URL is not configured.\n', status=503, content_type='text/plain; charset=utf-8')

    root = Element('urlset', xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')
    routes = ['', '/entreprise', '/expertises', '/realisations', '/certificats', '/actualites', '/contact']
    for route in routes:
        node = SubElement(root, 'url')
        SubElement(node, 'loc').text = f'{origin}{route}/' if route and route != '/' else f'{origin}/'
    for route, queryset in (
        ('realisations', Project.objects.filter(is_published=True)),
        ('actualites', Article.objects.filter(is_published=True)),
    ):
        for item in queryset.only('slug', 'updated_at'):
            node = SubElement(root, 'url')
            SubElement(node, 'loc').text = f'{origin}/{route}/{item.slug}'
            SubElement(node, 'lastmod').text = item.updated_at.date().isoformat()
    return HttpResponse(tostring(root, encoding='utf-8', xml_declaration=True), content_type='application/xml; charset=utf-8')
