import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router'
import { fetchJournal } from '../../api/moderation'
import Menu from '../../components/Menu'
import PageTitle from '../../components/PageTitle'
import Sheet from '../../components/Sheet'
import { ACTION_LABELS, actorLabel, detailLabel, teamDate } from '../../lib/moderation'
import TeamGuard from './TeamGuard'
import styles from './Team.module.css'

function what(e: { target_user_id: number | null; target_character_id: number | null; target_story_id: number | null }) {
  if (e.target_story_id) return <Link to={`/histoires/${e.target_story_id}`}>une histoire</Link>
  if (e.target_character_id) return <Link to={`/personnages/${e.target_character_id}`}>une fiche</Link>
  return null
}

function Journal() {
  const [params, setParams] = useSearchParams()
  const action = params.get('action') ?? ''
  const page = Number(params.get('page')) || 1
  const journal = useQuery({
    queryKey: ['moderation', 'journal', { action, page }],
    queryFn: () => fetchJournal({ action: action || undefined, page }),
    placeholderData: keepPreviousData,
  })
  const pages = Math.max(1, Math.ceil((journal.data?.total ?? 0) / 50))

  return (
    <main className={styles.page}>
      <PageTitle>Journal de modération</PageTitle>
      <div className={styles.head}>
        <h1>Journal</h1>
        <Link to="/equipe" className={styles.crumb}>
          Espace équipe
        </Link>
      </div>
      <Sheet seed="equipe-journal-page" contentClassName={styles.card}>
        <Menu
          label="Quelles actions"
          variant="compact"
          value={action}
          options={[{ value: '', label: 'Toutes' }, ...Object.entries(ACTION_LABELS).map(([value, label]) => ({ value, label }))]}
          onChange={(v) => setParams(v ? { action: v } : {})}
        />
        {journal.data?.items.length ? (
          <ul className={styles.list}>
            {journal.data.items.map((e) => (
              <li key={e.id} className={styles.row}>
                <span>
                  <strong>{ACTION_LABELS[e.action] ?? e.action}</strong>
                  {detailLabel(e.detail) && ` (${detailLabel(e.detail)})`}
                  {what(e) && <> · {what(e)}</>}
                  {e.target_user_id && (
                    <>
                      {' '}
                      · <Link to={`/equipe/comptes/${e.target_user_id}`}>compte n°{e.target_user_id}</Link>
                    </>
                  )}
                  <br />
                  <span className={styles.muted}>{e.reason}</span>
                </span>
                <span className={styles.muted}>
                  le {teamDate(e.created_at)}, {actorLabel(e.actor_id, e.action)}
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <p className={styles.muted}>{journal.isPending ? 'On ouvre le journal…' : 'Rien au journal pour l’instant.'}</p>
        )}
      </Sheet>
      {pages > 1 && (
        <nav className={styles.pagination} aria-label="Pages">
          <button type="button" disabled={page <= 1} onClick={() => setParams({ ...(action && { action }), page: String(page - 1) })}>
            Plus récentes
          </button>
          <span>
            Page {page} sur {pages}
          </span>
          <button type="button" disabled={page >= pages} onClick={() => setParams({ ...(action && { action }), page: String(page + 1) })}>
            Plus anciennes
          </button>
        </nav>
      )}
    </main>
  )
}

function JournalPage() {
  return (
    <TeamGuard>
      <Journal />
    </TeamGuard>
  )
}

export default JournalPage
