import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router'
import { fetchCases } from '../../api/moderation'
import PageTitle from '../../components/PageTitle'
import Sheet from '../../components/Sheet'
import { useCan } from '../../lib/useCan'
import TeamGuard from './TeamGuard'
import styles from './Team.module.css'

/** /equipe : les outils auxquels on a droit, chacun expliqué en une phrase (#80). */
function TeamHome() {
  const open = useQuery({ queryKey: ['moderation', 'cases', 'open'], queryFn: () => fetchCases('open') })
  const waiting = open.data?.total ?? 0
  const canManageRoles = useCan('manage_roles')

  return (
    <main className={styles.page}>
      <PageTitle>Espace équipe</PageTitle>
      <div className={styles.head}>
        <h1>Espace équipe</h1>
        <a href="/moderation" className={styles.crumb}>
          La charte de modération
        </a>
      </div>
      <div className={styles.tools}>
        <Sheet seed="equipe-signalements" contentClassName={`${styles.card} ${styles.tool}`}>
          <Link to="/equipe/signalements">Signalements</Link>
          <p className={styles.muted}>
            Les contenus signalés par les membres, un dossier par contenu. On lit, on masque si besoin, on tranche.
          </p>
          {waiting > 0 && (
            <span className={`${styles.badge} ${styles.alert}`}>
              {waiting} dossier{waiting > 1 ? 's' : ''} en attente
            </span>
          )}
        </Sheet>
        <Sheet seed="equipe-journal" contentClassName={`${styles.card} ${styles.tool}`}>
          <Link to="/equipe/journal">Journal</Link>
          <p className={styles.muted}>
            Chaque action de l'équipe, avec son auteur et sa raison. On s'y réfère pour relire une contestation.
          </p>
        </Sheet>
        {canManageRoles && (
          <Sheet seed="equipe-roles" contentClassName={`${styles.card} ${styles.tool}`}>
            <Link to="/equipe/roles">Rôles</Link>
            <p className={styles.muted}>Qui est modérateur ou admin, et donner un rôle à quelqu'un. Réservé aux admins.</p>
          </Sheet>
        )}
        <Sheet seed="equipe-pages" variant="muted" contentClassName={`${styles.card} ${styles.tool}`}>
          <strong>Sur les pages du site</strong>
          <p className={styles.muted}>
            Sur chaque fiche et chaque histoire, un encadré « Équipe » permet de masquer le contenu et d'ouvrir le compte de
            son propriétaire, sans passer par un signalement.
          </p>
        </Sheet>
      </div>
    </main>
  )
}

function TeamHomePage() {
  return (
    <TeamGuard>
      <TeamHome />
    </TeamGuard>
  )
}

export default TeamHomePage
