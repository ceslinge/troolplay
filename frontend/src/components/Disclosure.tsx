import { type ReactNode, useId, useState } from 'react'
import styles from './Disclosure.module.css'

type Props = {
  /** Ce qu'on peut ajouter, en clair : « Avertir le lecteur (facultatif) ». */
  label: string
  /** Ouvert d'office : déjà rempli, ou une erreur à y corriger. */
  open?: boolean
  children: ReactNode
}

/** Une option repliée derrière un lien : l'écran reste simple, et rien n'est caché pour de bon. */
function Disclosure({ label, open = false, children }: Props) {
  const id = useId()
  const [shown, setShown] = useState(open)
  const visible = shown || open
  return (
    <div className={styles.disclosure}>
      <button type="button" className={`action-link ${styles.toggle}`} aria-expanded={visible} aria-controls={id} onClick={() => setShown(!visible)}>
        <svg className={styles.chevron} viewBox="0 0 24 24" aria-hidden="true">
          <path d="M9 6l6 6-6 6" />
        </svg>
        {label}
      </button>
      <div id={id} className={styles.content} hidden={!visible}>
        {children}
      </div>
    </div>
  )
}

export default Disclosure
