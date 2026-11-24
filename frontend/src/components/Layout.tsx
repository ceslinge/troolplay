import { Link, NavLink, Outlet } from 'react-router'
import { useMyCharacters } from '../lib/activeCharacter'
import { LEGAL_PAGES } from '../lib/legal'
import { useMe } from '../lib/useMe'
import CharacterRail from './CharacterRail'
import styles from './Layout.module.css'

/** Le cadre de toutes les pages : l'en-tête, la barre de ses personnages, puis la page elle-même. */
function Layout() {
  const me = useMe()
  const mine = useMyCharacters()

  return (
    <div className={styles.shell}>
      {/* Au clavier, le premier Tab propose de sauter l'en-tête et la barre. */}
      <a href="#contenu" className={styles.skip}>
        Aller au contenu
      </a>
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
              me.data === null && (
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
        <div id="contenu" className={styles.main} tabIndex={-1}>
          <Outlet />
        </div>
      </div>
      <footer className={styles.footer}>
        <nav className={styles.inner} aria-label="Pied de page">
          <p className={styles.fan}>Un projet de fan, sans lien avec Ankama.</p>
          <ul className={styles.footerLinks}>
            {Object.values(LEGAL_PAGES).map((page) => (
              <li key={page.path}>
                <Link to={page.path} className={styles.link}>
                  {page.label}
                </Link>
              </li>
            ))}
          </ul>
        </nav>
      </footer>
    </div>
  )
}

export default Layout
