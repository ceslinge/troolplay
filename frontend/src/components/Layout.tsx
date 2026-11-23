import { Link, NavLink, Outlet } from 'react-router'
import { useMe } from '../lib/useMe'
import styles from './Layout.module.css'

/** Le cadre de toutes les pages : l'en-tête, puis la page elle-même. */
function Layout() {
  const me = useMe()

  return (
    <>
      <header className={styles.header}>
        <div className={styles.inner}>
          <Link to="/" className={styles.brand}>
            TroolPlay
          </Link>
          <nav className={styles.nav} aria-label="Principale">
            <NavLink to="/communaute" className={styles.link}>
              Communauté
            </NavLink>
            {me.data ? (
              <>
                <NavLink to="/compte" className={styles.link}>
                  Mon compte
                </NavLink>
                <Link to="/personnages/nouveau" className={styles.cta}>
                  Épingler un personnage
                </Link>
              </>
            ) : (
              !me.isPending && (
                <Link to="/connexion" className={styles.cta}>
                  Se connecter
                </Link>
              )
            )}
          </nav>
        </div>
      </header>
      <Outlet />
    </>
  )
}

export default Layout
