import type { ReactNode } from 'react'
import { useScrollToHash } from '../lib/useScrollToHash'
import Sheet from './Sheet'
import styles from './AccountSection.module.css'

type Props = {
  title: string
  /** La graine du papier : chaque feuille a son grain. */
  seed: string
  /** Pour un lien direct, comme celui des mails (#decisions, #demandes). */
  id?: string
  /** Contenu arrivé : on peut descendre jusqu'ici si l'adresse le demande. */
  ready?: boolean
  children: ReactNode
}

/** Une rubrique de Mon compte : son titre sur une étiquette, puis une feuille. */
function AccountSection({ title, seed, id, ready = true, children }: Props) {
  // Le lien d'un mail mène ici : on y descend une fois le contenu arrivé.
  useScrollToHash(id, ready)

  return (
    <section className={styles.section} id={id}>
      <h2 className={styles.title}>{title}</h2>
      <Sheet seed={seed} contentClassName={styles.card}>
        {children}
      </Sheet>
    </section>
  )
}

export default AccountSection
