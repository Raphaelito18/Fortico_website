import { useEffect, useState } from 'react'
import { Link, NavLink, Route, Routes, useLocation, useParams } from 'react-router-dom'
import { detailMetadata, detailPath } from './seo.js'
import './App.css'

const apiBase = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '')
const currentYear = new Date().getFullYear()

const navItems = [
  ['Nos expertises', '/expertises'],
  ['Réalisations', '/realisations'],
  ['À propos', '/entreprise'],
  ['Certificats', '/certificats'],
  ['Actualités', '/actualites'],
]

const provisionalExpertises = [
  { title: 'Systèmes embarqués', summary: 'Firmware, électronique, PCB, IoT et solutions connectées.' },
  { title: 'Instrumentation industrielle', summary: 'Mesure, supervision, contrôle et acquisition de données.' },
  { title: 'Automatisation', summary: 'Contrôle, supervision, robotique et smart building.' },
  { title: 'Électricité et maintenance', summary: 'Installations, dépannage préventif et curatif.' },
]

async function apiGet(path, signal) {
  const response = await fetch(`${apiBase}/v1/${path}`, { signal })
  if (!response.ok) throw new Error(`Erreur HTTP ${response.status}`)
  const payload = await response.json()
  return payload.results ?? payload
}

function useApi(path) {
  const [state, setState] = useState({ path: '', data: null, error: '', loading: true })

  useEffect(() => {
    const controller = new AbortController()
    apiGet(path, controller.signal)
      .then((data) => setState({ path, data, error: '', loading: false }))
      .catch((error) => {
        if (error.name !== 'AbortError') {
          setState({ path, data: null, error: error.message === 'Erreur HTTP 404' ? 'not-found' : 'Le contenu est momentanément indisponible.', loading: false })
        }
      })
    return () => controller.abort()
  }, [path])

  return state.path === path ? state : { path, data: null, error: '', loading: true }
}

function assetUrl(path) {
  if (!path || /^(?:[a-z]+:)?\/\//i.test(path)) return path
  const apiOrigin = apiBase.startsWith('/') ? window.location.origin : new URL(apiBase).origin
  return new URL(path, apiOrigin).href
}

function Brand({ footer = false }) {
  return (
    <Link className={`brand${footer ? ' footer-brand' : ''}`} to="/" aria-label="FORTICO Madagascar, accueil">
      <img src="/fortico-logo.jpg" alt="FORTICO — Ingénierie électronique embarquée et automatismes" />
    </Link>
  )
}

function RouteMetadata() {
  const { pathname } = useLocation()
  useEffect(() => {
    const page = navItems.find(([, path]) => path === pathname)?.[0]
    const titles = { '/': 'Accueil', '/entreprise': 'À propos', '/expertises': 'Nos expertises', '/realisations': 'Réalisations', '/contact': 'Contact', '/certificats': 'Certificats et références', '/actualites': 'Actualités' }
    const descriptions = {
      '/': 'Découvrez FORTICO Madagascar : présentation de l’entreprise, expertises, réalisations et contact.',
      '/entreprise': 'Présentation, mission et valeurs de FORTICO Madagascar.',
      '/expertises': 'Les domaines d’intervention publiés par FORTICO Madagascar.',
      '/realisations': 'Une sélection des projets publiés par l’entreprise.',
      '/certificats': 'Les documents et références publiés par FORTICO Madagascar.',
      '/actualites': 'Les nouvelles et publications de FORTICO Madagascar.',
      '/contact': 'Écrivez à l’équipe FORTICO Madagascar.',
    }
    const title = `${titles[pathname] || page || 'Page introuvable'} — FORTICO Madagascar`
    const description = descriptions[pathname] || 'Le lien est peut-être incorrect ou la page a été déplacée.'
    document.title = title
    document.querySelector('meta[name="description"]')?.setAttribute('content', description)
    document.querySelector('meta[property="og:title"]')?.setAttribute('content', title)
    document.querySelector('meta[property="og:description"]')?.setAttribute('content', description)
  }, [pathname])
  return null
}

function DetailMetadata({ item, kind }) {
  useEffect(() => {
    if (!item) return
    const { title, description, type, image } = detailMetadata(item, kind)
    const setMeta = (selector, value) => {
      let element = document.querySelector(selector)
      if (!element) {
        element = document.createElement('meta')
        const [, key, name] = selector.match(/meta\[(name|property)="([^"]+)"\]/)
        element.setAttribute(key, name)
        document.head.append(element)
      }
      element.content = value
    }
    document.title = title
    setMeta('meta[name="description"]', description)
    setMeta('meta[property="og:type"]', type)
    setMeta('meta[property="og:title"]', title)
    setMeta('meta[property="og:description"]', description)
    if (image) setMeta('meta[property="og:image"]', assetUrl(image))
    else document.querySelector('meta[property="og:image"]')?.remove()
    const publicSiteUrl = (import.meta.env.VITE_PUBLIC_SITE_URL || '').replace(/\/$/, '')
    let canonical = document.querySelector('link[rel="canonical"]')
    if (publicSiteUrl) {
      if (!canonical) {
        canonical = document.createElement('link')
        canonical.rel = 'canonical'
        document.head.append(canonical)
      }
      canonical.href = `${publicSiteUrl}${window.location.pathname}`
      setMeta('meta[property="og:url"]', canonical.href)
    } else {
      canonical?.remove()
      document.querySelector('meta[property="og:url"]')?.remove()
    }
    return () => {
      document.querySelector('link[rel="canonical"]')?.remove()
      document.querySelector('meta[property="og:url"]')?.remove()
      document.querySelector('meta[property="og:image"]')?.remove()
    }
  }, [item, kind])
  return null
}

function Header() {
  const [menuOpen, setMenuOpen] = useState(false)
  return (
    <header className="site-header">
      <div className="header-inner wrap">
        <Brand />
        <button className="menu-toggle" type="button" aria-expanded={menuOpen} aria-controls="main-nav" onClick={() => setMenuOpen(!menuOpen)}>
          <span className="sr-only">{menuOpen ? 'Fermer le menu' : 'Ouvrir le menu'}</span><span /><span />
        </button>
        <nav id="main-nav" className={menuOpen ? 'main-nav is-open' : 'main-nav'} aria-label="Navigation principale" onClick={() => setMenuOpen(false)}>
          <NavLink to="/" end>Accueil</NavLink>
          {navItems.map(([label, path]) => <NavLink key={path} to={path}>{label}</NavLink>)}
          <NavLink className="nav-contact" to="/contact">Parlons de votre projet <span aria-hidden="true">→</span></NavLink>
        </nav>
      </div>
    </header>
  )
}

function Footer() {
  const { data: company } = useApi('company/')
  return (
    <footer className="site-footer">
      <div className="wrap footer-main">
        <Brand footer />
        <p className="footer-description">{company?.short_description || 'Ingénierie électronique embarquée et automatismes. Les informations détaillées seront complétées par FORTICO.'}</p>
        <div className="footer-contact">
          <Link className="footer-action" to="/contact"><span aria-hidden="true">✉</span> Nous contacter <span aria-hidden="true">→</span></Link>
          {company?.city && <span>⌖ &nbsp;{company.city}{company.country ? `, ${company.country}` : ''}</span>}
          {company?.email && <a href={`mailto:${company.email}`}>✉ &nbsp;{company.email}</a>}
          {company?.phone && <a href={`tel:${company.phone}`}>☎ &nbsp;{company.phone}</a>}
        </div>
      </div>
      <div className="wrap footer-bottom"><span>© {currentYear} FORTICO Madagascar</span><span>Informations et visuels en cours de validation</span></div>
    </footer>
  )
}

function PageIntro({ eyebrow = 'FORTICO MADAGASCAR', title, description }) {
  return <div className="page-intro"><p className="eyebrow">{eyebrow}</p><h1>{title}</h1>{description && <p className="intro-copy">{description}</p>}</div>
}

function HomePage() {
  const { data: company, error: companyError } = useApi('company/')
  const { data: expertise, error: expertiseError, loading: expertiseLoading } = useApi('expertises/')
  const { data: projects, error: projectsError, loading: projectsLoading } = useApi('projects/')
  const hasExpertises = expertise?.length > 0

  return (
    <main>
      <section className="hero wrap">
        <div className="hero-copy">
          <p className="eyebrow"><span className="eyebrow-line" /> FORTICO · MADAGASCAR</p>
          <h1>{company?.slogan || <><span>Des solutions techniques</span><br /><span className="hero-secondary">pour un monde <br className="mobile-only-break" /><em>plus intelligent.</em></span></>}</h1>
          <p className="hero-description">{company?.short_description || 'Nous concevons, intégrons et maintenons des solutions fiables en électronique, électricité, instrumentation industrielle, systèmes embarqués et automatisation.'}</p>
          <div className="hero-actions"><Link className="button button-primary" to="/expertises">Découvrir nos expertises <span aria-hidden="true">→</span></Link><Link className="button button-outline" to="/realisations">Voir nos projets</Link></div>
          {(!company?.slogan || !company?.short_description) && <p className="content-note">Texte de présentation proposé par la maquette — à confirmer par FORTICO.</p>}
          {companyError && <p className="content-note">{companyError}</p>}
        </div>
        <div className="hero-visual"><img src="/hero-engineering.svg" alt="Illustration technique d’une carte électronique, d’une armoire d’instrumentation et d’un bras robotisé" fetchPriority="high" /></div>
      </section>

      <section className="expertise-section" aria-labelledby="expertise-heading">
        <div className="wrap">
          <div className="expertise-caption"><p className="eyebrow" id="expertise-heading">NOS EXPERTISES</p><Link className="text-link" to="/expertises">Toutes nos expertises <span aria-hidden="true">→</span></Link></div>
          {expertiseLoading ? <p className="empty-state">Chargement des expertises…</p> : hasExpertises ? <ExpertiseCards items={expertise} /> : <><ExpertiseCards items={provisionalExpertises} provisional /><p className="provisional-note">Domaines proposés dans la maquette, à confirmer par FORTICO.{expertiseError ? ` ${expertiseError}` : ''}</p></>}
        </div>
      </section>

      <section className="projects-section wrap" aria-labelledby="projects-heading">
        <div className="projects-intro"><p className="eyebrow">NOS PROJETS</p><h2 id="projects-heading">Des solutions concrètes pour vos projets</h2><p>Découvrez les réalisations publiées par FORTICO et validées pour présentation.</p><Link className="text-link" to="/realisations">Voir tous nos projets <span aria-hidden="true">→</span></Link></div>
        <div className="projects-content">{projectsLoading ? <p className="empty-state">Chargement des réalisations…</p> : <ContentGrid items={projects} kind="project" error={projectsError} limit={3} />}</div>
      </section>
    </main>
  )
}

function ExpertiseIcon({ index }) {
  const paths = [
    <><rect x="7" y="7" width="18" height="18" rx="2" /><path d="M12 2v5m8-5v5m-8 18v5m8-5v5M2 12h5m-5 8h5m18-8h5m-5 8h5M12 12h8v8h-8z" /></>,
    <><circle cx="16" cy="16" r="12" /><path d="M16 8v8l6 4M9 26h14M12 4l-2 3m12-3 2 3" /></>,
    <><path d="M16 4 6 13h7l-2 10 12-12h-8l1-7Z" /><circle cx="25" cy="7" r="2" /><path d="M25 9v5m-3-3h6" /></>,
    <><path d="M17 2 7 17h8l-1 13 11-17h-8l1-11Z" /></>,
  ]
  return <span className="expertise-icon"><svg viewBox="0 0 32 32" role="img" aria-label="">{paths[index % paths.length]}</svg></span>
}

function ExpertiseCards({ items, provisional = false }) {
  return <div className="expertise-grid">{items.slice(0, 4).map((item, index) => <article className="expertise-card" key={item.id || item.slug || item.title}><ExpertiseIcon index={index} /><h3>{item.title}</h3><p>{item.summary || item.description}</p>{!provisional && item.image && <img className="expertise-thumb" src={assetUrl(item.image)} alt={item.alt_text || ''} loading="lazy" />}</article>)}</div>
}

function ContentGrid({ items, kind, error = '', limit }) {
  if (error) return <p className="empty-state" role="status">{error}</p>
  if (!items?.length) {
    const emptyMessage = kind === 'article'
      ? 'Aucune actualité publiée pour le moment.'
      : kind === 'expertise'
        ? 'Aucune expertise publiée pour le moment.'
        : 'Aucune réalisation publiée pour le moment. Les projets seront ajoutés après validation par FORTICO.'
    return <p className="empty-state">{emptyMessage}</p>
  }
  return <div className={`content-grid ${kind === 'project' ? 'project-grid' : ''}`}>{items.slice(0, limit || items.length).map((item, index) => {
    const card = <><div className="card-image">{item.image ? <img src={assetUrl(item.image)} alt={item.alt_text || ''} loading="lazy" /> : <div className={`image-placeholder placeholder-${index % 3}`}><span>Image à ajouter</span></div>}</div><div className="card-body"><p className="card-meta">{kind === 'project' ? [item.sector, item.location].filter(Boolean).join(' · ') || 'Réalisation' : kind === 'article' ? item.category || 'Actualité' : item.icon || 'Expertise'}</p><h3>{item.title}</h3><p>{item.summary || item.excerpt || item.description || ''}</p></div></>
    return kind === 'project' || kind === 'article'
      ? <Link className="content-card" key={item.id || item.slug} to={detailPath(kind, item.slug)}>{card}</Link>
      : <article className="content-card" key={item.id || item.slug}>{card}</article>
  })}</div>
}

function DetailPage({ kind }) {
  const isArticle = kind === 'article'
  const { slug } = useParams()
  const { data, error, loading } = useApi(`${isArticle ? 'articles' : 'projects'}/${slug}/`)
  const listPath = isArticle ? '/actualites' : '/realisations'
  if (loading) return <main className="wrap inner-page"><p className="empty-state" role="status">Chargement du contenu…</p></main>
  if (error) return error === 'not-found' ? <NotFoundPage /> : <main className="wrap inner-page"><p className="empty-state" role="alert">{error}</p><Link className="text-link" to={listPath}>Retour à la liste</Link></main>
  if (!data) return <NotFoundPage />
  const description = isArticle ? (data.excerpt || '') : (data.summary || '')
  const body = isArticle ? (data.content || data.excerpt || '') : (data.description || data.summary || '')
  const paragraphs = body.split(/\n\s*\n/).filter(Boolean)
  const images = isArticle ? [] : (data.images || []).map((entry) => entry.image || entry.url).filter(Boolean)
  const date = isArticle ? data.published_date : data.completed_date
  return <main className="wrap inner-page detail-page"><DetailMetadata item={data} kind={kind} /><Link className="text-link detail-back" to={listPath}>← Retour à {isArticle ? 'l’actualité' : 'nos réalisations'}</Link><PageIntro eyebrow={isArticle ? 'ACTUALITÉ' : 'RÉALISATION'} title={data.title} description={description} />
    {data.image && <img className="detail-image" src={assetUrl(data.image)} alt={data.alt_text || ''} />}
    <div className="detail-facts">{isArticle ? data.category?.name && <span>{data.category.name}</span> : [data.client_name, data.sector, data.location].filter(Boolean).map((value) => <span key={value}>{value}</span>)}{date && <time dateTime={date}>{date}</time>}{isArticle && data.author && <span>{data.author}</span>}</div>
    {paragraphs.length > 0 && <div className="detail-content">{paragraphs.map((paragraph, index) => <p key={index}>{paragraph}</p>)}</div>}
    {images.length > 0 && <div className="detail-gallery">{images.map((image, index) => <img key={`${image}-${index}`} src={assetUrl(image)} alt={data.alt_text || `${data.title} — image ${index + 1}`} loading="lazy" />)}</div>}
    <Link className="button button-outline" to={listPath}>Retour à la liste <span aria-hidden="true">→</span></Link>
  </main>
}

function CompanyPage() {
  const { data: company, error, loading } = useApi('company/')
  return <main className="wrap inner-page"><PageIntro title="À propos de FORTICO" description={company?.short_description || 'Les informations institutionnelles seront publiées ici après validation par l’équipe FORTICO.'} />{loading ? <p className="empty-state">Chargement des informations…</p> : error ? <p className="empty-state" role="status">{error}</p> : <div className="company-details"><section><p className="eyebrow">À PROPOS</p><h2>Présentation</h2><p>{company?.description || 'La présentation officielle de l’entreprise est en préparation.'}</p></section><section><p className="eyebrow">NOTRE MISSION</p><h2>Mission</h2><p>{company?.mission || 'Les informations seront ajoutées par l’équipe FORTICO.'}</p></section><section><p className="eyebrow">NOS VALEURS</p><h2>Valeurs</h2>{company?.values?.length ? <ul className="values-list">{company.values.map((value) => <li key={value}>{value}</li>)}</ul> : <p>Les informations seront ajoutées par l’équipe FORTICO.</p>}</section></div>}</main>
}

function ListingPage({ title, description, endpoint, kind, eyebrow }) {
  const { data, error, loading } = useApi(endpoint)
  return <main className="wrap inner-page"><PageIntro eyebrow={eyebrow} title={title} description={description} />{loading ? <p className="empty-state">Chargement du contenu…</p> : <ContentGrid items={data} kind={kind} error={error} />}</main>
}

function CertificatesPage() {
  const { data, error, loading } = useApi('certificates/')
  return <main className="wrap inner-page"><PageIntro eyebrow="RÉFÉRENCES" title="Certificats & références" description="Les documents et références de l’entreprise seront présentés dans cet espace." />{loading ? <p className="empty-state">Chargement des références…</p> : error ? <p className="empty-state" role="status">{error}</p> : data?.length ? <div className="certificate-grid">{data.map((item) => <article className="certificate-card" key={item.id || item.slug}><span className="certificate-icon" aria-hidden="true">✳</span><p className="card-meta">{item.issuer || 'Référence'}</p><h2>{item.title}</h2>{item.description && <p>{item.description}</p>}{item.document && <a className="text-link" href={assetUrl(item.document)} target="_blank" rel="noreferrer">Consulter le document ↗</a>}</article>)}</div> : <p className="empty-state">Aucun certificat ou référence publié pour le moment.</p>}</main>
}

function ContactPage() {
  const [status, setStatus] = useState({ type: '', message: '' })
  const [sending, setSending] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    setSending(true)
    setStatus({ type: '', message: '' })
    const form = event.currentTarget
    const values = Object.fromEntries(new FormData(form))
    try {
      const response = await fetch(`${apiBase}/v1/contact/`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(values) })
      const payload = await response.json().catch(() => ({}))
      if (!response.ok) throw new Error(Object.values(payload).flat().join(' ') || 'Votre message n’a pas pu être envoyé.')
      form.reset()
      setStatus({ type: 'success', message: payload.message || 'Votre message a bien été envoyé.' })
    } catch (error) {
      setStatus({ type: 'error', message: error.message || 'Une erreur est survenue. Réessayez dans quelques instants.' })
    } finally {
      setSending(false)
    }
  }

  return <main className="wrap inner-page contact-page"><PageIntro eyebrow="CONTACT" title="Parlons de votre projet." description="Écrivez à l’équipe FORTICO Madagascar. Les coordonnées directes seront affichées dès leur confirmation." /><div className="contact-layout"><div className="contact-aside"><p className="eyebrow">VOTRE MESSAGE</p><p>Les champs marqués d’un astérisque sont obligatoires. Votre demande est transmise à l’équipe FORTICO.</p></div><form className="contact-form" onSubmit={handleSubmit}><label htmlFor="contact-name">Nom complet <span>*</span></label><input id="contact-name" name="name" autoComplete="name" minLength="2" maxLength="150" required /><label htmlFor="contact-email">Adresse e-mail <span>*</span></label><input id="contact-email" type="email" name="email" autoComplete="email" maxLength="254" required /><label htmlFor="contact-subject">Objet <span>*</span></label><input id="contact-subject" name="subject" minLength="3" maxLength="200" required /><label htmlFor="contact-message">Votre message <span>*</span></label><textarea id="contact-message" name="message" rows="6" minLength="10" required /><button className="button button-primary" type="submit" disabled={sending}>{sending ? 'Envoi en cours…' : 'Envoyer le message'} <span aria-hidden="true">→</span></button>{status.message && <p className={`form-status ${status.type}`} role="status">{status.message}</p>}</form></div></main>
}

function NotFoundPage() {
  return <main className="wrap not-found"><p className="eyebrow">ERREUR 404</p><h1>Cette page n’existe pas.</h1><p>Le lien est peut-être incorrect ou la page a été déplacée.</p><Link className="button button-primary" to="/">Retour à l’accueil <span aria-hidden="true">→</span></Link></main>
}

function App() {
  return <><RouteMetadata /><a className="skip-link" href="#main-content">Aller au contenu</a><Header /><div id="main-content" tabIndex="-1"><Routes><Route path="/" element={<HomePage />} /><Route path="/entreprise" element={<CompanyPage />} /><Route path="/expertises" element={<ListingPage eyebrow="SAVOIR-FAIRE" title="Nos expertises" description="Les domaines d’intervention publiés par FORTICO Madagascar." endpoint="expertises/" kind="expertise" />} /><Route path="/realisations" element={<ListingPage eyebrow="PROJETS" title="Nos réalisations" description="Une sélection des projets publiés par l’entreprise." endpoint="projects/" kind="project" />} /><Route path="/realisations/:slug" element={<DetailPage kind="project" />} /><Route path="/certificats" element={<CertificatesPage />} /><Route path="/actualites" element={<ListingPage eyebrow="JOURNAL" title="Actualités & publications" description="Les nouvelles et publications de FORTICO Madagascar." endpoint="articles/" kind="article" />} /><Route path="/actualites/:slug" element={<DetailPage kind="article" />} /><Route path="/contact" element={<ContactPage />} /><Route path="*" element={<NotFoundPage />} /></Routes></div><Footer /></>
}

export default App
