import { Link, NavLink, Outlet } from 'react-router'
import { useMyCharacters } from '../lib/activeCharacter'
import { useMe } from '../lib/useMe'
import CharacterRail from './CharacterRail'
import styles from './Layout.module.css'

/** Le cadre de toutes les pages : l'en-tête, la barre de ses personnages, puis la page elle-même. */
function Layout() {
  const me = useMe()
  const mine = useMyCharacters()

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
                {/* Avec des personnages, le « + » de la barre suffit. */}
                {mine?.length === 0 && (
                  <Link to="/personnages/nouveau" className={styles.cta}>
                    Présenter mon premier personnage
                  </Link>
                )}
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
      <div className={styles.body}>
        <CharacterRail />
        <div className={styles.main}>
          <Outlet />
        </div>
      </div>
    </>
  )
}

export default Layout
