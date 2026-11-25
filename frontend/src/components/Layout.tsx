import { Link, NavLink, Outlet, useLocation } from 'react-router'
import { useMyCharacters } from '../lib/activeCharacter'
import { LEGAL_PAGES } from '../lib/legal'
import { useCan } from '../lib/useCan'
import { useMe } from '../lib/useMe'
import SuspendedPage from '../pages/SuspendedPage'
import CharacterRail from './CharacterRail'
import Wordmark from './Wordmark'
import styles from './Layout.module.css'

/** Le cadre de toutes les pages : l'en-tête, la barre de ses personnages, puis la page elle-même. */
function Layout() {
  const me = useMe()
  const mine = useMyCharacters()
  const team = useCan('moderate')
  const { pathname } = useLocation()
  // Un compte suspendu ne voit que sa suspension, et les pages légales pour lire les règles (#141).
  const suspended = me.data?.suspended ? me.data : null
  const legal = Object.values(LEGAL_PAGES).some((page) => page.path === pathname)

  return (
    <div className={styles.shell}>
      {/* Au clavier, le premier Tab propose de sauter l'en-tête et la barre. */}
      <a href="#contenu" className={styles.skip}>
        Aller au contenu
      </a>
      <header className={styles.header}>
        <div className={styles.inner}>
          {/* Le R et le P tracés à la plume : le RP se lit dans le nom (#108). */}
          <Link to="/" className={styles.brand} aria-label="tRoolPlay, accueil">
            <Wordmark />
          </Link>
          <nav className={styles.nav} aria-label="Principale">
            {/* Suspendu, la Communauté le ramènerait à sa suspension : on ne la propose pas. */}
            {!suspended && (
              <NavLink to="/communaute" className={styles.link}>
                Communauté
              </NavLink>
            )}
            {suspended ? (
              <NavLink to="/compte" className={styles.link}>
                Mon compte
              </NavLink>
            ) : me.data ? (
              <>
                {/* Pour écrire, il faut un personnage qui signe : sans lui, le bouton du premier personnage suffit. */}
                {(mine?.length ?? 0) > 0 && (
                  <NavLink to="/histoires/nouvelle" className={styles.link}>
                    Écrire
                  </NavLink>
                )}
                {team && (
                  <NavLink to="/equipe" className={styles.link}>
                    Équipe
                  </NavLink>
                )}
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
        {!suspended && <CharacterRail />}
        <div id="contenu" className={styles.main} tabIndex={-1}>
          {suspended && !legal ? <SuspendedPage until={suspended.suspended_until} /> : <Outlet />}
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
