import type { SupportMessage } from '../api/support'
import styles from './ConversationThread.module.css'

type Props = {
  messages: SupportMessage[]
  /** Vu de l'équipe : on nomme le compte du membre et qui, dans l'équipe, a répondu. */
  team?: { userId: number }
}

const when = (iso: string) => new Date(iso).toLocaleString('fr-FR', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })

/** Les messages d'une conversation avec l'équipe, du premier au dernier. */
function ConversationThread({ messages, team }: Props) {
  return (
    <ol className={styles.thread}>
      {messages.map((m) => (
        <li key={m.id} className={m.from_team ? styles.team : styles.member}>
          <p className={styles.meta}>
            {m.from_team
              ? team
                ? `L'équipe (compte n°${m.author_id ?? '?'})`
                : "L'équipe"
              : team
                ? `Le membre (compte n°${team.userId})`
                : 'Toi'}
            , le {when(m.created_at)}
          </p>
          <p className={styles.body}>{m.body}</p>
        </li>
      ))}
    </ol>
  )
}

export default ConversationThread
