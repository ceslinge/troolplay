import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link, useSearchParams } from 'react-router'
import { answerContest, fetchContests, type Outcome, type TeamContest } from '../../api/moderation'
import Notice from '../../components/Notice'
import PageTitle from '../../components/PageTitle'
import ReasonForm from '../../components/ReasonForm'
import Sheet from '../../components/Sheet'
import { ACTION_LABELS, entryDetail, hasTarget, OUTCOME_LABELS, teamDate } from '../../lib/moderation'
import JournalTarget from './JournalTarget'
import TeamGuard from './TeamGuard'
import styles from './Team.module.css'

const OUTCOME_HINTS: Record<Outcome, string> = {
  upheld: 'La décision reste. La personne reçoit ta réponse par mail.',
  lifted: 'Le site lève la mesure tout de suite (contenu rétabli, compte rouvert, droit de signaler rendu), et le note au journal.',
}

function Answer({ contest, onDone }: { contest: TeamContest; onDone: () => void }) {
  const queryClient = useQueryClient()
  const [outcome, setOutcome] = useState<Outcome | null>(null)
  const answer = useMutation({
    mutationFn: (text: string) => answerContest(contest.id, outcome!, text),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['moderation'] })
      onDone()
    },
  })
  return (
    <ReasonForm
      title="Répondre à la contestation"
      confirm="Envoyer la réponse"
      busy={answer.isPending}
      error={answer.error}
      hint="Envoyée à la personne par mail, et gardée au journal."
      ready={outcome !== null}
      onConfirm={(text) => answer.mutate(text)}
      onCancel={onDone}
    >
      <fieldset className={styles.choices}>
        {(Object.keys(OUTCOME_LABELS) as Outcome[]).map((o) => (
          <label key={o}>
            <input type="radio" name="issue" checked={outcome === o} onChange={() => setOutcome(o)} />
            <span>
              Décision {OUTCOME_LABELS[o].toLowerCase()}
              <small>{OUTCOME_HINTS[o]}</small>
            </span>
          </label>
        ))}
      </fieldset>
    </ReasonForm>
  )
}

function ContestCard({ contest }: { contest: TeamContest }) {
  const [answering, setAnswering] = useState(false)
  const d = contest.decision
  return (
    <Sheet seed={`contestation-${contest.id}`} contentClassName={styles.card}>
      <h2>
        {ACTION_LABELS[d.action] ?? d.action}
        {entryDetail(d) && ` (${entryDetail(d)})`}
        {hasTarget(d) && (
          <>
            {' '}
            · <JournalTarget entry={d} />
          </>
        )}
        {contest.target_name && ` « ${contest.target_name} »`}
      </h2>
      <p className={styles.muted}>
        Décidé le {teamDate(d.created_at)} : {d.reason}
        {contest.contester_id && (
          <>
            {' '}
            · <Link to={`/equipe/comptes/${contest.contester_id}`}>compte n°{contest.contester_id}</Link> (
            <Link to={`/equipe/comptes/${contest.contester_id}#historique`}>son historique</Link>)
          </>
        )}
      </p>
      <p>
        <strong>La contestation, le {teamDate(contest.created_at)} :</strong>
      </p>
      <blockquote className={styles.quote}>{contest.body}</blockquote>
      {contest.outcome ? (
        <p>
          <strong>Décision {OUTCOME_LABELS[contest.outcome].toLowerCase()}</strong>
          {contest.answered_at && <span className={styles.muted}> le {teamDate(contest.answered_at)}</span>} : {contest.answer}
        </p>
      ) : answering ? (
        <Answer contest={contest} onDone={() => setAnswering(false)} />
      ) : (
        <>
          {contest.decided_by_me && (
            <Notice>
              <p>C'est toi qui as pris cette décision : si possible, laisse un autre membre de l'équipe la relire.</p>
            </Notice>
          )}
          <div>
            <button type="button" className="action-link" onClick={() => setAnswering(true)}>
              Répondre
            </button>
          </div>
        </>
      )}
    </Sheet>
  )
}

/** /equipe/contestations : un message par décision contestée, une réponse par contestation (#141). */
function Contests() {
  const [params] = useSearchParams()
  const status = params.get('statut') === 'traitees' ? 'answered' : 'open'
  const contests = useQuery({ queryKey: ['moderation', 'contests', status], queryFn: () => fetchContests(status) })

  return (
    <main className={styles.page}>
      <PageTitle>Contestations</PageTitle>
      <div className={styles.head}>
        <h1>Contestations</h1>
        <Link to="/equipe" className={styles.crumb}>
          Espace équipe
        </Link>
      </div>
      <nav className={styles.tabs} aria-label="Contestations">
        <Link to="/equipe/contestations" aria-current={status === 'open' ? 'page' : undefined}>
          En attente
        </Link>
        <Link to="/equipe/contestations?statut=traitees" aria-current={status === 'answered' ? 'page' : undefined}>
          Traitées
        </Link>
      </nav>
      {contests.isError ? (
        <Notice tone="error">
          <p>Impossible de charger les contestations pour l'instant.</p>
        </Notice>
      ) : contests.data?.items.length === 0 ? (
        <Sheet seed="contestations-vide" contentClassName={styles.card}>
          <p className={styles.muted}>{status === 'open' ? 'Aucune contestation en attente.' : 'Aucune contestation traitée pour l’instant.'}</p>
        </Sheet>
      ) : (
        contests.data?.items.map((c) => <ContestCard key={c.id} contest={c} />)
      )}
    </main>
  )
}

function ContestsPage() {
  return (
    <TeamGuard>
      <Contests />
    </TeamGuard>
  )
}

export default ContestsPage
