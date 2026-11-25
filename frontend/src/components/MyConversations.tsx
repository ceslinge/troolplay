import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { type Conversation, fetchMyConversations, replyAsMember, startConversation, type Topic } from '../api/support'
import { conversationState, TOPIC_LABELS } from '../lib/support'
import AccountSection from './AccountSection'
import Chips from './Chips'
import ConversationThread from './ConversationThread'
import Disclosure from './Disclosure'
import MessageForm from './MessageForm'
import Notice from './Notice'
import styles from './MyConversations.module.css'

const TOPICS = (Object.keys(TOPIC_LABELS) as Topic[]).map((value) => ({ value, label: TOPIC_LABELS[value] }))

function useRefresh() {
  const queryClient = useQueryClient()
  return () => queryClient.invalidateQueries({ queryKey: ['conversations'] })
}

function NewRequest({ onDone }: { onDone: () => void }) {
  const refresh = useRefresh()
  const [topic, setTopic] = useState<Topic | undefined>()
  const send = useMutation({
    mutationFn: (body: string) => startConversation(topic!, body),
    onSuccess: () => {
      refresh()
      onDone()
    },
  })
  return (
    <MessageForm
      label="Ton message"
      confirm="Envoyer à l'équipe"
      hint="L'équipe te répond ici, et te prévient par mail."
      busy={send.isPending}
      error={send.error}
      ready={topic !== undefined}
      onSend={(body) => send.mutate(body)}
      onCancel={onDone}
    >
      <Chips legend="C'est à propos de" options={TOPICS} value={topic} onChange={setTopic} />
    </MessageForm>
  )
}

function Reply({ conversation }: { conversation: Conversation }) {
  const refresh = useRefresh()
  const [open, setOpen] = useState(false)
  const send = useMutation({
    mutationFn: (body: string) => replyAsMember(conversation.id, body),
    onSuccess: () => {
      refresh()
      setOpen(false)
    },
  })
  if (!open) {
    return (
      <button type="button" className="action-link" onClick={() => setOpen(true)}>
        Répondre
      </button>
    )
  }
  return (
    <MessageForm label="Ta réponse" confirm="Envoyer" busy={send.isPending} error={send.error} onSend={(body) => send.mutate(body)} onCancel={() => setOpen(false)} />
  )
}

/** Dans Mon compte : écrire à l'équipe, et suivre ses demandes (#142). */
function MyConversations() {
  const conversations = useQuery({ queryKey: ['conversations'], queryFn: fetchMyConversations })
  const [writing, setWriting] = useState(false)

  return (
    <AccountSection title="Écrire à l'équipe" seed="compte-demandes" id="demandes" ready={conversations.isSuccess}>
      <p className="hint">
        Une question, un problème avec ton compte, un bug : l'équipe te lit. Pour contester une décision, passe plutôt par
        la décision elle-même.
      </p>
      {writing ? (
        <NewRequest onDone={() => setWriting(false)} />
      ) : (
        <div>
          <button type="button" className="action-link" onClick={() => setWriting(true)}>
            Nouvelle demande
          </button>
        </div>
      )}
      {conversations.isError && (
        <Notice tone="error">
          <p>Impossible de charger tes demandes pour l'instant.</p>
        </Notice>
      )}
      {conversations.data?.map((c) => (
        <Disclosure key={c.id} label={`${TOPIC_LABELS[c.topic]}, ${conversationState(c)}`} open={!c.closed_at && !c.waiting_for_team}>
          <div className={styles.conversation}>
            <ConversationThread messages={c.messages} />
            {c.closed_at ? <p className="hint">Cette demande est close. Pour autre chose, ouvre-en une nouvelle.</p> : <Reply conversation={c} />}
          </div>
        </Disclosure>
      ))}
    </AccountSection>
  )
}

export default MyConversations
