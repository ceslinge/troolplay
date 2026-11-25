import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link, useSearchParams } from 'react-router'
import { closeConversation, fetchTeamConversations, type Queue, replyAsTeam, type TeamConversation } from '../../api/support'
import ConversationThread from '../../components/ConversationThread'
import MessageForm from '../../components/MessageForm'
import Notice from '../../components/Notice'
import PageTitle from '../../components/PageTitle'
import Sheet from '../../components/Sheet'
import { teamDate } from '../../lib/moderation'
import { TOPIC_LABELS } from '../../lib/support'
import TeamGuard from './TeamGuard'
import styles from './Team.module.css'

const QUEUES: { queue: Queue; param: string | null; label: string; empty: string }[] = [
  { queue: 'waiting', param: null, label: 'À répondre', empty: 'Personne n’attend de réponse.' },
  { queue: 'answered', param: 'repondues', label: 'Répondues', empty: 'Aucune demande en attente du membre.' },
  { queue: 'closed', param: 'closes', label: 'Closes', empty: 'Aucune demande close.' },
]

function Request({ conversation }: { conversation: TeamConversation }) {
  const queryClient = useQueryClient()
  const [replying, setReplying] = useState(false)
  const done = () => queryClient.invalidateQueries({ queryKey: ['moderation', 'conversations'] })
  const reply = useMutation({
    mutationFn: (body: string) => replyAsTeam(conversation.id, body),
    onSuccess: () => {
      setReplying(false)
      done()
    },
  })
  const close = useMutation({ mutationFn: () => closeConversation(conversation.id), onSuccess: done })

  return (
    <Sheet seed={`demande-${conversation.id}`} contentClassName={styles.card}>
      <h2>
        {TOPIC_LABELS[conversation.topic]} · <Link to={`/equipe/comptes/${conversation.user_id}`}>compte n°{conversation.user_id}</Link>
      </h2>
      <p className={styles.muted}>
        Ouverte le {teamDate(conversation.created_at)}
        {conversation.closed_at && `, close le ${teamDate(conversation.closed_at)}`}
      </p>
      <ConversationThread messages={conversation.messages} team={{ userId: conversation.user_id }} />
      {!conversation.closed_at &&
        (replying ? (
          <MessageForm
            label="Ta réponse"
            confirm="Envoyer la réponse"
            hint="Le membre la lit dans son compte ; un mail le prévient, sans le contenu."
            busy={reply.isPending}
            error={reply.error}
            onSend={(body) => reply.mutate(body)}
            onCancel={() => setReplying(false)}
          />
        ) : (
          <div className={styles.rowActions}>
            <button type="button" className="action-link" onClick={() => setReplying(true)}>
              Répondre
            </button>
            <button type="button" className="action-link" disabled={close.isPending} onClick={() => close.mutate()}>
              Clore la demande
            </button>
          </div>
        ))}
    </Sheet>
  )
}

/** /equipe/demandes : ce que les membres écrivent à l'équipe (#142). */
function Requests() {
  const [params] = useSearchParams()
  const current = QUEUES.find((q) => q.param === params.get('file')) ?? QUEUES[0]
  const requests = useQuery({
    queryKey: ['moderation', 'conversations', current.queue],
    queryFn: () => fetchTeamConversations(current.queue),
  })

  return (
    <main className={styles.page}>
      <PageTitle>Demandes</PageTitle>
      <div className={styles.head}>
        <h1>Demandes</h1>
        <Link to="/equipe" className={styles.crumb}>
          Espace équipe
        </Link>
      </div>
      <nav className={styles.tabs} aria-label="Demandes">
        {QUEUES.map((q) => (
          <Link key={q.queue} to={q.param ? `/equipe/demandes?file=${q.param}` : '/equipe/demandes'} aria-current={q === current ? 'page' : undefined}>
            {q.label}
          </Link>
        ))}
      </nav>
      {requests.isError ? (
        <Notice tone="error">
          <p>Impossible de charger les demandes pour l'instant.</p>
        </Notice>
      ) : requests.data?.items.length === 0 ? (
        <Sheet seed="demandes-vide" contentClassName={styles.card}>
          <p className={styles.muted}>{current.empty}</p>
        </Sheet>
      ) : (
        requests.data?.items.map((c) => <Request key={c.id} conversation={c} />)
      )}
    </main>
  )
}

function RequestsPage() {
  return (
    <TeamGuard>
      <Requests />
    </TeamGuard>
  )
}

export default RequestsPage
