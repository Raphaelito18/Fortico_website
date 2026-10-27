export function detailPath(kind, slug) {
  const section = kind === 'article' ? 'actualites' : 'realisations'
  return `/${section}/${encodeURIComponent(slug)}`
}

export function detailMetadata(item, kind) {
  const isArticle = kind === 'article'
  const source = isArticle ? (item.excerpt || item.content) : (item.summary || item.description)
  const fallback = isArticle
    ? 'Actualités et publications de FORTICO Madagascar.'
    : 'Réalisation publiée par FORTICO Madagascar.'
  const description = (source || fallback)
    .replace(/<[^>]*>/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .slice(0, 200)
  return {
    title: `${item.title} — FORTICO Madagascar`,
    description,
    type: isArticle ? 'article' : 'website',
    image: item.image || '',
  }
}
