import type { ReactNode } from 'react'
import Sheet from './Sheet'
import styles from './AccountSection.module.css'

type Props = {
  title: string
  /** La graine du papier : chaque feuille a son grain. */
  seed: string
  /** Pour un lien direct, comme celui des mails de décision (#decisions). */
  id?: string
  children: ReactNode
}

/** Une rubrique de Mon compte : son titre sur une étiquette, puis une feuille. */
function AccountSection({ title, seed, id, children }: Props) {
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
