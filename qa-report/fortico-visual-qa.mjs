import { createRequire } from 'node:module'
import { mkdir, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'

const require = createRequire(resolve('frontend/package.json'))
const { chromium } = require('playwright')

const baseUrl = process.env.FORTICO_BASE_URL || 'http://127.0.0.1:5173'
const runId = new Date().toISOString().replace(/[:.]/g, '-')
const screenshotDir = resolve('qa-report', `screenshots-${runId}`)
const resultsPath = resolve('qa-report', `visual-qa-results-${runId}.json`)
const dimensions = [
  { width: 360, height: 800 },
  { width: 390, height: 844 },
  { width: 768, height: 1024 },
  { width: 1440, height: 900 },
]
const routeCases = [
  ['home', '/'],
  ['expertises', '/expertises'],
  ['realisations', '/realisations'],
  ['detail-realisation-empty', '/realisations/qa-route-inexistante'],
  ['entreprise', '/entreprise'],
  ['certificats', '/certificats'],
  ['actualites', '/actualites'],
  ['detail-article-empty', '/actualites/qa-route-inexistante'],
  ['contact', '/contact'],
  ['404', '/qa-page-inexistante'],
]

await mkdir(screenshotDir, { recursive: true })
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe',
})
const results = { browser: await browser.version(), baseUrl, matrix: [], interactions: {}, consoleErrors: [], pageErrors: [], consoleWarnings: [], resourceErrors: [], failedRequests: [], requestAborts: [], httpErrors: [], imageFailures: [] }

function observe(page) {
  page.on('console', (message) => {
    const entry = { pageUrl: page.url(), text: message.text(), location: message.location().url }
    if (message.type() === 'error' && message.text().includes('Failed to load resource')) results.resourceErrors.push(entry)
    else if (message.type() === 'error') results.consoleErrors.push(entry)
    else if (message.type() === 'warning') results.consoleWarnings.push(entry)
  })
  page.on('pageerror', (error) => results.pageErrors.push({ url: page.url(), text: error.message }))
  page.on('requestfailed', (request) => {
    const error = request.failure()?.errorText || 'request failed'
    const entry = { url: request.url(), error }
    if (error === 'net::ERR_ABORTED') results.requestAborts.push(entry)
    else results.failedRequests.push(entry)
  })
  page.on('response', (response) => {
    if (response.status() >= 400) results.httpErrors.push({ url: response.url(), status: response.status() })
  })
  page.on('requestfinished', async (request) => {
    if (request.resourceType() !== 'image') return
    try {
      const response = await request.response()
      if (!response || (!response.ok() && response.status() !== 304)) results.imageFailures.push({ url: request.url(), status: response?.status() })
    } catch {
      results.imageFailures.push({ url: request.url(), status: 'unavailable' })
    }
  })
}

async function inspectPage(context, name, path, viewport, screenshot = false) {
  const page = await context.newPage()
  await page.setViewportSize(viewport)
  observe(page)
  await page.goto(`${baseUrl}${path}`, { waitUntil: 'networkidle' })
  await page.locator('main').waitFor()
  const measurement = await page.evaluate(() => ({
    title: document.title,
    documentWidth: document.documentElement.scrollWidth,
    viewportWidth: window.innerWidth,
    mainText: document.querySelector('main')?.innerText.slice(0, 250) || '',
    footerVisible: Boolean(document.querySelector('footer.site-footer')),
    footerBottom: document.querySelector('footer.site-footer')?.getBoundingClientRect().bottom || 0,
    viewportHeight: window.innerHeight,
    imageStates: [...document.images].map((image) => ({ src: image.currentSrc, loaded: image.complete && image.naturalWidth > 0 })),
  }))
  const overflow = measurement.documentWidth > measurement.viewportWidth + 1
  const shortPageFooterGap = measurement.documentWidth === measurement.viewportWidth && measurement.footerBottom < measurement.viewportHeight - 1 && measurement.mainText.includes('Aucune')
  const brokenImages = measurement.imageStates.filter((image) => !image.loaded)
  results.matrix.push({ name, path, viewport, overflow, shortPageFooterGap, ...measurement, brokenImages })
  if (screenshot) {
    const size = `${viewport.width}x${viewport.height}`
    await page.screenshot({ path: resolve(screenshotDir, `${name}-${size}.png`), fullPage: true })
  }
  await page.close()
  return { overflow, brokenImages }
}

try {
  // Inspect every defined page at all requested sizes against the real local API.
  const context = await browser.newContext()
  for (const viewport of dimensions) {
    for (const [name, path] of routeCases) {
      const shouldCapture = name === 'home' || name === 'contact' || viewport.width === 1440
      await inspectPage(context, name, path, viewport, shouldCapture)
    }
  }

  // Mobile navigation: it opens, exposes its destinations, and closes after navigation.
  for (const viewport of dimensions.filter((item) => item.width < 821)) {
    const page = await context.newPage()
    await page.setViewportSize(viewport)
    observe(page)
    await page.goto(`${baseUrl}/`, { waitUntil: 'networkidle' })
    const toggle = page.getByRole('button', { name: 'Ouvrir le menu' })
    await toggle.click()
    const nav = page.getByRole('navigation', { name: 'Navigation principale' })
    const expanded = await nav.isVisible()
    await nav.getByRole('link', { name: 'Certificats' }).click()
    results.interactions[`mobileMenu-${viewport.width}`] = {
      opened: expanded,
      navigatedTo: new URL(page.url()).pathname,
      collapsedAfterNavigation: await page.getByRole('button', { name: 'Ouvrir le menu' }).getAttribute('aria-expanded') === 'false',
    }
    await page.close()
  }

  // Real anonymous contact submission to the development PostgreSQL database.
  const contactPage = await context.newPage()
  await contactPage.setViewportSize({ width: 390, height: 844 })
  observe(contactPage)
  await contactPage.goto(`${baseUrl}/contact`, { waitUntil: 'networkidle' })
  const form = contactPage.locator('form.contact-form')
  const submit = form.getByRole('button', { name: /Envoyer le message/ })
  await submit.click()
  const emptyFormBlocked = await contactPage.locator('#contact-name').evaluate((input) => !input.validity.valid)
  await contactPage.locator('#contact-name').fill('QA Visiteur')
  await contactPage.locator('#contact-email').fill('adresse-invalide')
  const invalidEmailBlocked = await contactPage.locator('#contact-email').evaluate((input) => !input.validity.valid)
  await contactPage.locator('#contact-subject').fill('Test QA navigation')
  await contactPage.locator('#contact-message').fill('Message QA temporaire pour valider le parcours de contact.')
  const invalidSubmissionBlocked = await contactPage.locator('#contact-email').evaluate((input) => !input.validity.valid)
  results.interactions.contactClientValidation = { emptyFormBlocked, invalidEmailBlocked, invalidSubmissionBlocked }

  const qaMarker = `QA-BROWSER-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
  await contactPage.locator('#contact-email').fill(`${qaMarker.toLowerCase()}@example.invalid`)
  await contactPage.locator('#contact-subject').fill(qaMarker)
  const contactResponsePromise = contactPage.waitForResponse((response) => response.url().includes('/api/v1/contact/') && response.request().method() === 'POST')
  await submit.click()
  const contactResponse = await contactResponsePromise
  await contactPage.getByRole('status').waitFor()
  results.interactions.contactSubmission = {
    status: contactResponse.status(),
    requestUrl: contactResponse.url(),
    requestMethod: contactResponse.request().method(),
    authorizationHeaderPresent: Boolean((await contactResponse.request().allHeaders()).authorization),
    response: await contactResponse.json(),
    successVisible: (await contactPage.getByRole('status').innerText()).includes('Merci'),
    formReset: await contactPage.locator('#contact-name').inputValue() === '',
    buttonReenabled: await submit.isEnabled(),
    marker: qaMarker,
  }
  await contactPage.close()

  const invalidApiPage = await context.newPage()
  await invalidApiPage.setViewportSize({ width: 390, height: 844 })
  observe(invalidApiPage)
  await invalidApiPage.goto(`${baseUrl}/contact`, { waitUntil: 'networkidle' })
  await invalidApiPage.locator('form.contact-form').evaluate((element) => element.setAttribute('novalidate', ''))
  await invalidApiPage.locator('#contact-name').fill('A')
  await invalidApiPage.locator('#contact-email').fill('adresse-invalide')
  await invalidApiPage.locator('#contact-subject').fill('x')
  await invalidApiPage.locator('#contact-message').fill('court')
  const invalidResponsePromise = invalidApiPage.waitForResponse((response) => response.url().includes('/api/v1/contact/') && response.request().method() === 'POST')
  await invalidApiPage.locator('form.contact-form button[type="submit"]').click()
  const invalidResponse = await invalidResponsePromise
  await invalidApiPage.getByRole('status').waitFor()
  results.interactions.invalidApiSubmission = {
    status: invalidResponse.status(),
    message: await invalidApiPage.getByRole('status').innerText(),
    buttonReenabled: await invalidApiPage.locator('form.contact-form button[type="submit"]').isEnabled(),
  }
  await invalidApiPage.close()

  // Exercise an API error state and an HTTP 429 state without additional backend writes.
  const errorPage = await context.newPage()
  await errorPage.setViewportSize({ width: 390, height: 844 })
  observe(errorPage)
  await errorPage.route('**/api/v1/expertises/**', (route) => route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ detail: 'API QA indisponible' }) }))
  await errorPage.goto(`${baseUrl}/expertises`, { waitUntil: 'networkidle' })
  results.interactions.apiErrorState = await errorPage.getByRole('status').innerText()
  await errorPage.close()

  const throttledPage = await context.newPage()
  await throttledPage.setViewportSize({ width: 390, height: 844 })
  observe(throttledPage)
  await throttledPage.route('**/api/v1/contact/', (route) => route.fulfill({ status: 429, contentType: 'application/json', body: JSON.stringify({ detail: 'Trop de demandes. Réessayez plus tard.' }) }))
  await throttledPage.goto(`${baseUrl}/contact`, { waitUntil: 'networkidle' })
  await throttledPage.locator('#contact-name').fill('QA Visiteur')
  await throttledPage.locator('#contact-email').fill('qa-rate-limit@example.invalid')
  await throttledPage.locator('#contact-subject').fill('Essai limité')
  await throttledPage.locator('#contact-message').fill('Soumission QA simulant une réponse de limite de débit.')
  await throttledPage.locator('form.contact-form button[type="submit"]').click()
  const throttledStatus = throttledPage.getByRole('status')
  await throttledStatus.waitFor()
  results.interactions.rateLimitState = {
    message: await throttledStatus.innerText(),
    buttonReenabled: await throttledPage.locator('form.contact-form button[type="submit"]').isEnabled(),
    responseStatus: 429,
  }
  await throttledPage.close()

  // Use an in-memory browser-only fixture to prove detail cards navigate and render.
  // No business rows are added to PostgreSQL.
  const fixtureContext = await browser.newContext({ viewport: { width: 1440, height: 900 } })
  const fixturePage = await fixtureContext.newPage()
  observe(fixturePage)
  const project = { id: 9001, title: 'Fixture QA — projet', slug: 'fixture-qa-projet', sector: 'Essai navigateur', location: 'Données temporaires', summary: 'Contenu simulé uniquement dans le navigateur.', description: 'Description de recette.', image: null, images: [] }
  const articleList = { id: 9002, title: 'Fixture QA — article', slug: 'fixture-qa-article', category: 'Essai navigateur', excerpt: 'Contenu simulé uniquement dans le navigateur.', image: null }
  const articleDetail = { ...articleList, category: { name: 'Essai navigateur' }, content: 'Texte de recette.' }
  await fixturePage.route('**/api/v1/projects/**', async (route) => {
    const url = new URL(route.request().url())
    await route.fulfill({ contentType: 'application/json', body: JSON.stringify(url.pathname.endsWith('/fixture-qa-projet/') ? project : [project]) })
  })
  await fixturePage.route('**/api/v1/articles/**', async (route) => {
    const url = new URL(route.request().url())
    await route.fulfill({ contentType: 'application/json', body: JSON.stringify(url.pathname.endsWith('/fixture-qa-article/') ? articleDetail : [articleList]) })
  })
  await fixturePage.goto(`${baseUrl}/realisations`, { waitUntil: 'networkidle' })
  await fixturePage.getByRole('link', { name: /Fixture QA — projet/ }).click()
  await fixturePage.getByRole('heading', { name: project.title }).waitFor()
  await fixturePage.screenshot({ path: resolve(screenshotDir, 'detail-realisation-browser-fixture-1440x900.png'), fullPage: true })
  const projectDetailWorks = new URL(fixturePage.url()).pathname === `/realisations/${project.slug}`
  await fixturePage.goto(`${baseUrl}/actualites`, { waitUntil: 'networkidle' })
  await fixturePage.getByRole('link', { name: /Fixture QA — article/ }).click()
  await fixturePage.getByRole('heading', { name: articleDetail.title }).waitFor()
  await fixturePage.screenshot({ path: resolve(screenshotDir, 'detail-article-browser-fixture-1440x900.png'), fullPage: true })
  const articleDetailWorks = new URL(fixturePage.url()).pathname === `/actualites/${articleDetail.slug}`
  results.interactions.detailCards = { projectDetailWorks, articleDetailWorks, fixtureStoredInDatabase: false }
  await fixtureContext.close()

  // Screenshot representative content and contact error states at all four sizes.
  for (const viewport of dimensions) {
    const page = await context.newPage()
    await page.setViewportSize(viewport)
    observe(page)
    await page.goto(`${baseUrl}/`, { waitUntil: 'networkidle' })
    await page.screenshot({ path: resolve(screenshotDir, `home-${viewport.width}x${viewport.height}.png`), fullPage: true })
    await page.goto(`${baseUrl}/contact`, { waitUntil: 'networkidle' })
    await page.screenshot({ path: resolve(screenshotDir, `contact-${viewport.width}x${viewport.height}.png`), fullPage: true })
    await page.close()
  }

  await context.close()
} finally {
  await browser.close()
}

await writeFile(resultsPath, JSON.stringify(results, null, 2), 'utf8')
console.log(JSON.stringify({ browser: results.browser, matrixCount: results.matrix.length, interactions: results.interactions, consoleErrors: results.consoleErrors, pageErrors: results.pageErrors, consoleWarnings: results.consoleWarnings, resourceErrors: results.resourceErrors, failedRequests: results.failedRequests, requestAbortCount: results.requestAborts.length, httpErrors: results.httpErrors, imageFailures: results.imageFailures, screenshots: screenshotDir, resultsPath }, null, 2))
