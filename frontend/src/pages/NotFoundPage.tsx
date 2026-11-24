import { Link } from 'react-router'
import buttons from '../components/Button.module.css'
import StatusPage from '../components/StatusPage'

/** Une adresse qui ne mène nulle part : on le dit simplement, et on propose où aller. */
function NotFoundPage() {
  return (
    <StatusPage
      tab="Page introuvable"
      icon="compass"
      title="Cette page n'est pas sur le panneau"
      lead="L'adresse est peut-être mal tapée, ou la page a été retirée depuis. Rien de grave : le reste du panneau est toujours là."
    >
      <Link to="/" className={`${buttons.button} ${buttons.primary}`}>
        Retour à l'accueil
      </Link>
      <Link to="/communaute" className={`${buttons.button} ${buttons.secondary}`}>
        Voir la communauté
      </Link>
    </StatusPage>
  )
}

export default NotFoundPage
