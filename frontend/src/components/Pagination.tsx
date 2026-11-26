import styles from './Pagination.module.css'

type Props = {
  page: number
  pages: number
  onPage: (page: number) => void
  /** « Précédents / Suivants », ou « Plus récentes / Plus anciennes » selon la liste. */
  previous: string
  next: string
  className?: string
}

/** Passer d'une page de liste à l'autre. Rien quand tout tient sur une page. */
function Pagination({ page, pages, onPage, previous, next, className }: Props) {
  if (pages <= 1) return null
  return (
    <nav className={`${styles.pagination} ${className ?? ''}`} aria-label="Pages">
      <button type="button" disabled={page <= 1} onClick={() => onPage(page - 1)}>
        {previous}
      </button>
      <span>
        Page {page} sur {pages}
      </span>
      <button type="button" disabled={page >= pages} onClick={() => onPage(page + 1)}>
        {next}
      </button>
    </nav>
  )
}

export default Pagination
