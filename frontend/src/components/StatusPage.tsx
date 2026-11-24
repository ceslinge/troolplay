import type { ReactNode } from 'react'
import Medallion from './Medallion'
import type { IconName } from './Icon'
import PageTitle from './PageTitle'
import Sheet from './Sheet'
import styles from './StatusPage.module.css'

type Props = {
  /** Le titre de l'onglet. */
  tab: string
  icon: IconName
  title: string
  lead: string
  /** Les boutons ou liens proposés pour repartir. */
  children: ReactNode
}

/** Une page qui n'a rien d'autre à dire qu'un contretemps : une adresse inconnue, un panneau injoignable. */
function StatusPage({ tab, icon, title, lead, children }: Props) {
  return (
    <main className={styles.page}>
      <PageTitle>{tab}</PageTitle>
      <Sheet seed={icon} as="section" variant="muted" contentClassName={styles.card}>
        <Medallion icon={icon} tone="dark" />
        <h1 className={styles.title}>{title}</h1>
        <p className={styles.lead}>{lead}</p>
        <div className={styles.actions}>{children}</div>
      </Sheet>
    </main>
  )
}

export default StatusPage
