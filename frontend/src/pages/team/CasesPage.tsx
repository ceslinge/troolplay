import { useQuery } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router'
import { fetchCases } from '../../api/moderation'
import PageTitle from '../../components/PageTitle'
import Sheet from '../../components/Sheet'
import { REASON_LABELS, teamDate } from '../../lib/moderation'
import TeamGuard from './TeamGuard'
import styles from './Team.module.css'

function Cases() {
  const [params] = useSearchParams()
  const status = params.get('statut') === 'traites' ? 'closed' : 'open'
  const cases = useQuery({ queryKey: ['moderation', 'cases', status], queryFn: () => fetchCases(status) })

  return (
    <main className={styles.page}>
      <PageTitle>Signalements</PageTitle>
      <div className={styles.head}>
        <h1>Signalements</h1>
        <Link to="/equipe" className={styles.crumb}>
          Espace équipe
        </Link>
      </div>
      <nav className={styles.tabs} aria-label="Dossiers">
        <Link to="/equipe/signalements" aria-current={status === 'open' ? 'page' : undefined}>
          En attente
        </Link>
        <Link to="/equipe/signalements?statut=traites" aria-current={status === 'closed' ? 'page' : undefined}>
          Traités
        </Link>
      </nav>
      <Sheet seed={`equipe-dossiers-${status}`} contentClassName={styles.card}>
        {cases.isPending ? (
          <p className={styles.muted}>On parcourt les dossiers…</p>
        ) : cases.isError ? (
          <p className={styles.muted}>Impossible de charger les dossiers pour l'instant.</p>
        ) : cases.data.items.length === 0 ? (
          <p className={styles.muted}>{status === 'open' ? 'Rien en attente. Le panneau est calme.' : 'Aucun dossier traité pour l’instant.'}</p>
        ) : (
          <ul className={styles.list}>
            {cases.data.items.map((c) => (
              <li key={`${c.target}-${c.target_id}`} className={styles.row}>
                <span>
                  <strong>
                    <Link to={`/equipe/signalements/${c.target === 'character' ? 'personnage' : 'histoire'}/${c.target_id}`}>
                      {c.label}
                    </Link>
                  </strong>{' '}
                  <span className={styles.muted}>
                    {c.target === 'character' ? 'Fiche' : 'Histoire'}
                    {!c.exists && ', supprimée depuis'} · dernier signalement le {teamDate(c.last_reported_at)}
                  </span>
                </span>
                <span className={styles.badges}>
                  {status === 'open' && (
                    <span className={`${styles.badge} ${styles.alert}`}>
                      {c.open_reports} en attente
                    </span>
                  )}
                  {c.auto_hidden ? (
                    <span className={`${styles.badge} ${styles.alert}`}>Masqué automatiquement</span>
                  ) : (
                    c.hidden && <span className={styles.badge}>Masqué</span>
                  )}
                  {Object.entries(c.reasons).map(([reason, n]) => (
                    <span key={reason} className={styles.badge}>
                      {REASON_LABELS[reason as keyof typeof REASON_LABELS]}
                      {n && n > 1 ? ` ×${n}` : ''}
                    </span>
                  ))}
                </span>
              </li>
            ))}
          </ul>
        )}
      </Sheet>
    </main>
  )
}

function CasesPage() {
  return (
    <TeamGuard>
      <Cases />
    </TeamGuard>
  )
}

export default CasesPage
