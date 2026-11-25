import { Link } from 'react-router'
import buttons from './Button.module.css'
import AccountSection from './AccountSection'

/** Récupérer ce que le site garde de moi (#55) : un fichier, tout de suite. */
function MyData() {
  return (
    <AccountSection title="Mes données" seed="compte-donnees" id="donnees">
      <p className="hint">
        Un fichier avec tout ce que le site garde de toi : ton compte, tes personnages et leurs lieux, tes histoires et
        brouillons, les personnages que tu ignores, tes signalements, les décisions qui te concernent et tes échanges avec
        l'équipe. Au format JSON, lisible par un autre site comme par toi. Le détail est dans la{' '}
        <Link to="/confidentialite">page de confidentialité</Link>.
      </p>
      <div>
        <a href="/api/me/export" download className={`${buttons.button} ${buttons.secondary}`}>
          Télécharger mes données
        </a>
      </div>
    </AccountSection>
  )
}

export default MyData
