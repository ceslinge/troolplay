import { Link, useLocation } from 'react-router'
import buttons from './Button.module.css'
import Sheet from './Sheet'
import styles from './MembersOnly.module.css'

/** Les histoires se lisent connecté (décision 25) : on invite, sans rien montrer. */
function MembersOnly() {
  const { pathname, search } = useLocation()
  const next = encodeURIComponent(pathname + search)
  return (
    <Sheet seed="reserve-aux-membres" variant="muted" as="section" contentClassName={styles.card}>
      <p className={styles.text}>
        Les histoires sont réservées aux membres du panneau. Connecte-toi pour les lire, ou crée ton compte : c'est
        gratuit.
      </p>
      <div className={styles.actions}>
        <Link to={`/connexion?suite=${next}`} className={`${buttons.button} ${buttons.primary}`}>
          Se connecter
        </Link>
        <Link to="/inscription" className={`${buttons.button} ${buttons.secondary}`}>
          Créer un compte
        </Link>
      </div>
    </Sheet>
  )
}

export default MembersOnly
