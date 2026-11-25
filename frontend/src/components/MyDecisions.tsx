import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link } from 'react-router'
import { contestDecision, fetchMyDecisions, type MyDecision } from '../api/moderation'
import { DURATION_LABELS, OUTCOME_LABELS } from '../lib/moderation'
import AccountSection from './AccountSection'
import MessageForm from './MessageForm'
import Notice from './Notice'
import styles from './MyDecisions.module.css'

const CONTEST_MAX = 2000

const longDate = (iso: string) => new Date(iso).toLocaleDateString('fr-FR', { dateStyle: 'long' })

/** Ce que dit la décision, côté personne visée. */
function title(d: MyDecision): string {
  const what = d.target_story_id ? 'Ton histoire' : 'Ta fiche'
  const name = d.target_name ? ` « ${d.target_name} »` : ''
  switch (d.action) {
    case 'hide':
      return `${what}${name} a été masquée`
    case 'auto_hide':
      return `${what}${name} a été masquée en attendant qu'un modérateur la relise`
    case 'suspend':
      return `Compte suspendu${d.detail && d.detail in DURATION_LABELS ? ` (${DURATION_LABELS[d.detail as keyof typeof DURATION_LABELS].toLowerCase()})` : ''}`
    case 'revoke_reporting':
      return 'Droit de signaler retiré'
    default:
      return 'Décision de l’équipe'
  }
}

function ContestForm({ decision }: { decision: MyDecision }) {
  const queryClient = useQueryClient()
  const [open, setOpen] = useState(false)
  const send = useMutation({
    mutationFn: (body: string) => contestDecision(decision.id, body),
    onSuccess: (updated) => queryClient.setQueryData<MyDecision[]>(['decisions'], (all) => all?.map((d) => (d.id === updated.id ? updated : d))),
  })

  if (!open) {
    return (
      <button type="button" className="action-link" onClick={() => setOpen(true)}>
        Contester cette décision
      </button>
    )
  }
  return (
    <div className={styles.form}>
      <MessageForm
        label="Ce que tu veux dire à l'équipe"
        confirm="Envoyer ma contestation"
        hint="Un seul message par décision : prends le temps de tout dire. Un membre de l'équipe relira et te répondra par mail."
        busy={send.isPending}
        error={send.error}
        onSend={(body) => send.mutate(body)}
        onCancel={() => setOpen(false)}
        max={CONTEST_MAX}
      />
    </div>
  )
}

function Decision({ decision }: { decision: MyDecision }) {
  const { contest } = decision
  const link = decision.target_story_id
    ? `/histoires/${decision.target_story_id}`
    : decision.target_character_id
      ? `/personnages/${decision.target_character_id}`
      : null
  return (
    <li className={styles.decision}>
      <p className={styles.what}>
        <strong>{link && decision.target_name ? <Link to={link}>{title(decision)}</Link> : title(decision)}</strong>
        <span className={styles.date}>le {longDate(decision.created_at)}</span>
      </p>
      <p className={styles.reason}>La raison : {decision.reason}</p>
      {contest ? (
        <div className={styles.contest}>
          <p className={styles.label}>Ta contestation, le {longDate(contest.created_at)}</p>
          <p className={styles.quote}>{contest.body}</p>
          {contest.outcome ? (
            <p>
              <strong>Réponse de l'équipe : décision {OUTCOME_LABELS[contest.outcome].toLowerCase()}.</strong> {contest.answer}
            </p>
          ) : (
            <p className={styles.hint}>En attente de relecture par l'équipe.</p>
          )}
        </div>
      ) : (
        <ContestForm decision={decision} />
      )}
    </li>
  )
}

/** Les décisions de l'équipe qui me visent, chacune contestable une fois (#141). */
function MyDecisions({ always = false }: { always?: boolean }) {
  const decisions = useQuery({ queryKey: ['decisions'], queryFn: fetchMyDecisions })
  if (!always && !decisions.data?.length) return null
  return (
    <AccountSection title="Décisions de l'équipe" seed="compte-decisions" id="decisions" ready={decisions.isSuccess}>
      {decisions.isError ? (
        <Notice tone="error">
          <p>Impossible de charger les décisions pour l'instant.</p>
        </Notice>
      ) : decisions.data?.length === 0 ? (
        <p className={styles.hint}>Aucune décision ne te concerne.</p>
      ) : (
        <ul className={styles.list}>
          {decisions.data?.map((d) => (
            <Decision key={d.id} decision={d} />
          ))}
        </ul>
      )}
      <p className={styles.hint}>
        Les décisions suivent la <Link to="/moderation">charte de modération</Link>.
      </p>
    </AccountSection>
  )
}

export default MyDecisions
