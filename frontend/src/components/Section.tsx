import type { ReactNode } from 'react'
import type { IconName } from './Icon'
import Medallion from './Medallion'
import styles from './Section.module.css'

type Props = {
  id: string
  icon: IconName
  title: string
  children: ReactNode
  tone?: 'normal' | 'rumor'
}

/** Une partie de fiche : son médaillon, son titre, son contenu. */
function Section({ id, icon, title, children, tone = 'normal' }: Props) {
  return (
    <section id={id} className={styles.section}>
      <Medallion icon={icon} />
      <div className={styles.body}>
        <h2 className={`${styles.title} ${styles[tone]}`}>{title}</h2>
        {children}
      </div>
    </section>
  )
}

export default Section
