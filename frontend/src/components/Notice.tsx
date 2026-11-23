import type { ReactNode } from 'react'
import styles from './Notice.module.css'

type Props = {
  children: ReactNode
  tone?: 'info' | 'success' | 'error'
}

/** Un message à lire après une action : réussite, erreur, ou simple information. */
function Notice({ children, tone = 'info' }: Props) {
  return (
    <div className={`${styles.notice} ${styles[tone]}`} role={tone === 'error' ? 'alert' : 'status'}>
      {children}
    </div>
  )
}

export default Notice
