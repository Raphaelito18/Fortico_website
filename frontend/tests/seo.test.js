import test from 'node:test'
import assert from 'node:assert/strict'
import { detailMetadata, detailPath } from '../src/seo.js'

test('detail links point to the appropriate React routes and encode the slug', () => {
  assert.equal(detailPath('project', 'atelier-énergie'), '/realisations/atelier-%C3%A9nergie')
  assert.equal(detailPath('article', 'annonce-1'), '/actualites/annonce-1')
})

test('project metadata uses available content and image', () => {
  assert.deepEqual(detailMetadata({
    title: 'Projet publié',
    summary: 'Résumé réel.',
    image: '/api/v1/projects/projet/image/',
  }, 'project'), {
    title: 'Projet publié — FORTICO Madagascar',
    description: 'Résumé réel.',
    type: 'website',
    image: '/api/v1/projects/projet/image/',
  })
})

test('article metadata strips markup, caps description, and has a safe fallback', () => {
  const fromContent = detailMetadata({ title: 'Article', content: '<p>Texte <strong>publié</strong></p>' }, 'article')
  assert.equal(fromContent.description, 'Texte publié')
  assert.equal(fromContent.type, 'article')

  const fallback = detailMetadata({ title: 'Article sans résumé' }, 'article')
  assert.equal(fallback.description, 'Actualités et publications de FORTICO Madagascar.')

  const long = detailMetadata({ title: 'Long', excerpt: 'a'.repeat(240) }, 'article')
  assert.equal(long.description.length, 200)
})
