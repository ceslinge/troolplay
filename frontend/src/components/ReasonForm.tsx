import { type FormEvent, type ReactNode, useId, useState } from 'react'
import { ApiError } from '../api/client'
import FormActions from './FormActions'
import Notice from './Notice'
import styles from './ReasonForm.module.css'

type Props = {
  /** Ce qu'on s'apprête à faire, en clair : « Masquer cette histoire ». */
  title: string
  /** Ce que reçoit la personne concernée : la raison lui est envoyée par email. */
  hint?: string
  confirm: string
  danger?: boolean
  busy: boolean
  error: unknown
  onConfirm: (reason: string) => void
  onCancel: () => void
  /** Des choix en plus de la raison : une durée, une décision. */
  children?: ReactNode
  ready?: boolean
}

/** Toute action de l'équipe passe par ici : une raison écrite, toujours (charte de modération). */
function ReasonForm({ title, hint, confirm, danger, busy, error, onConfirm, onCancel, children, ready = true }: Props) {
  const id = useId()
  const [reason, setReason] = useState('')
  const failure = error instanceof ApiError ? error : null

  function submit(event: FormEvent) {
    event.preventDefault()
    if (reason.trim().length >= 3 && ready) onConfirm(reason.trim())
  }

  return (
    <form className={styles.form} onSubmit={submit} aria-labelledby={`${id}-titre`}>
      <h3 id={`${id}-titre`} className={styles.title}>
        {title}
      </h3>
      {failure && (
        <Notice tone="error">
          <p>{Object.values(failure.fields)[0] ?? failure.message}</p>
        </Notice>
      )}
      {children}
      <label className={styles.field}>
        <span className={styles.label}>La raison</span>
        <textarea value={reason} onChange={(event) => setReason(event.target.value)} rows={3} maxLength={1000} />
        <span className={styles.hint}>{hint ?? 'Elle est envoyée à la personne concernée, et gardée au journal.'}</span>
      </label>
      <FormActions confirm={confirm} onCancel={onCancel} busy={busy} disabled={reason.trim().length < 3 || !ready} danger={danger} />
    </form>
  )
}

export default ReasonForm
