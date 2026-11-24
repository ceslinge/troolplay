import { marked } from 'marked'
import type { MouseEvent } from 'react'
import { useNavigate } from 'react-router'
import PageTitle from '../components/PageTitle'
import Sheet from '../components/Sheet'
import { LEGAL_PAGES, type LegalPageName } from '../lib/legal'
import styles from './LegalPage.module.css'

const SOURCES = import.meta.glob<string>('../../../docs/legal/*.md', {
  query: '?raw',
  import: 'default',
  eager: true,
})

/** Le texte d'une page, avec les liens entre fichiers changés en adresses du site. */
function render(name: LegalPageName) {
  let text = SOURCES[`../../../docs/legal/${name}.md`] ?? ''
  for (const [file, page] of Object.entries(LEGAL_PAGES)) {
    text = text.replaceAll(`](${file}.md)`, `](${page.path})`)
  }
  return marked.parse(text, { async: false })
}

/** Règles, charte, confidentialité, mentions : des textes de docs/legal, mis en page. */
function LegalPage({ name }: { name: LegalPageName }) {
  const navigate = useNavigate()

  // Un lien vers une autre page du site reste dans le site, sans tout recharger.
  function follow(event: MouseEvent) {
    const link = (event.target as HTMLElement).closest('a')
    const href = link?.getAttribute('href')
    if (href?.startsWith('/') && !event.ctrlKey && !event.metaKey && !event.shiftKey) {
      event.preventDefault()
      navigate(href)
    }
  }

  return (
    <main className={styles.page}>
      <PageTitle>{LEGAL_PAGES[name].label}</PageTitle>
      <Sheet seed={name} as="article" contentClassName={styles.text}>
        {/* Nos propres textes, écrits dans le dépôt : pas de contenu de joueur ici. */}
        <div onClick={follow} dangerouslySetInnerHTML={{ __html: render(name) }} />
      </Sheet>
    </main>
  )
}

export default LegalPage
