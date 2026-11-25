import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router'
import { fetchJournal, fetchTeam, type TeamMember } from '../../api/moderation'
import Menu from '../../components/Menu'
import PageTitle from '../../components/PageTitle'
import Sheet from '../../components/Sheet'
import { ACTION_LABELS, actorLabel, entryDetail, hasTarget, teamDate } from '../../lib/moderation'
import JournalTarget from './JournalTarget'
import TeamGuard from './TeamGuard'
import styles from './Team.module.css'

const memberLabel = (m: TeamMember) => `compte n°${m.id}${m.characters.length ? ` (${m.characters.slice(0, 2).join(', ')})` : ''}`

function Journal() {
  const [params, setParams] = useSearchParams()
  const action = params.get('action') ?? ''
  const actor = params.get('par') ?? ''
  const page = Number(params.get('page')) || 1
  const journal = useQuery({
    queryKey: ['moderation', 'journal', { action, actor, page }],
    queryFn: () => fetchJournal({ action: action || undefined, actorId: Number(actor) || undefined, page }),
    placeholderData: keepPreviousData,
  })
  const team = useQuery({ queryKey: ['moderation', 'team'], queryFn: fetchTeam })
  const members = team.data ?? []
  // Un ancien membre de l'équipe n'est plus dans la liste, mais ses actions restent au journal.
  const people = [
    { value: '', label: 'Tout le monde' },
    ...members.map((m) => ({ value: String(m.id), label: memberLabel(m) })),
    ...(actor && !members.some((m) => String(m.id) === actor) ? [{ value: actor, label: `compte n°${actor}` }] : []),
  ]

  /** Les filtres restent, la page repart de 1 sauf si on la donne. */
  function show(changes: { action?: string; par?: string; page?: number }) {
    const next = { action, par: actor, ...changes }
    setParams({
      ...(next.action && { action: next.action }),
      ...(next.par && { par: next.par }),
      ...(changes.page && changes.page > 1 && { page: String(changes.page) }),
    })
  }
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
        <div className={styles.filters}>
          <Menu
            label="Quelles actions"
            variant="compact"
            value={action}
            options={[{ value: '', label: 'Toutes' }, ...Object.entries(ACTION_LABELS).map(([value, label]) => ({ value, label }))]}
            onChange={(v) => show({ action: v })}
          />
          <Menu label="Par qui" variant="compact" value={actor} options={people} onChange={(v) => show({ par: v })} />
        </div>
        {journal.data?.items.length ? (
          <ul className={styles.list}>
            {journal.data.items.map((e) => (
              <li key={e.id} className={styles.row}>
                <span>
                  <strong>{ACTION_LABELS[e.action] ?? e.action}</strong>
                  {entryDetail(e) && ` (${entryDetail(e)})`}
                  {hasTarget(e) && (
                    <>
                      {' '}
                      · <JournalTarget entry={e} />
                    </>
                  )}
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
                  le {teamDate(e.created_at)},{' '}
                  {e.actor_id && String(e.actor_id) !== actor ? (
                    <Link to={`?${new URLSearchParams({ ...(action && { action }), par: String(e.actor_id) })}`}>
                      {actorLabel(e.actor_id, e.action)}
                    </Link>
                  ) : (
                    actorLabel(e.actor_id, e.action)
                  )}
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
          <button type="button" disabled={page <= 1} onClick={() => show({ page: page - 1 })}>
            Plus récentes
          </button>
          <span>
            Page {page} sur {pages}
          </span>
          <button type="button" disabled={page >= pages} onClick={() => show({ page: page + 1 })}>
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
