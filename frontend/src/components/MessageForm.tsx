import { type FormEvent, type ReactNode, useState } from 'react'
import { ApiError } from '../api/client'
import { MESSAGE_MAX, MESSAGE_MIN } from '../api/support'
import Field from './Field'
import FormActions from './FormActions'
import Notice from './Notice'
import styles from './MessageForm.module.css'

type Props = {
  label: string
  confirm: string
  hint?: string
  busy: boolean
  error: unknown
  onSend: (body: string) => void
  onCancel: () => void
  /** Ce qu'on choisit en plus du message : le sujet d'une nouvelle demande. */
  children?: ReactNode
  ready?: boolean
  min?: number
  max?: number
}

/** Écrire un message : une demande à l'équipe, sa réponse, une contestation. */
function MessageForm({ label, confirm, hint, busy, error, onSend, onCancel, children, ready = true, min = MESSAGE_MIN, max = MESSAGE_MAX }: Props) {
  const [body, setBody] = useState('')
  const failure = error instanceof ApiError ? error : null
  const long = body.trim().length >= min

  function submit(event: FormEvent) {
    event.preventDefault()
    if (long && ready) onSend(body.trim())
  }

  return (
    <form className={styles.form} onSubmit={submit}>
      {children}
      <Field label={label} name="message" value={body} onChange={setBody} rows={4} maxLength={max} hint={hint} error={failure?.fields.body} />
      {failure && failure.status !== 422 && (
        <Notice tone="error">
          <p>{failure.message}</p>
        </Notice>
      )}
      <FormActions confirm={confirm} onCancel={onCancel} busy={busy} disabled={!long || !ready} />
    </form>
  )
}

export default MessageForm
