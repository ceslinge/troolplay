import { useMutation } from '@tanstack/react-query'
import { type FormEvent, useId, useState } from 'react'
import { ApiError } from '../api/client'
import { DETAILS_MAX, type ReportIn, type ReportReason, sendReport } from '../api/reports'
import { useMe } from '../lib/useMe'
import Button from './Button'
import Notice from './Notice'
import styles from './ReportButton.module.css'

// Dans l'ordre de la charte de modération : du hors-sujet au plus grave.
const REASONS: { value: ReportReason; label: string }[] = [
  { value: 'off_topic', label: 'Hors sujet : monde réel, politique, religion réelle' },
  { value: 'disrespect', label: 'Manque de respect, attaque contre un joueur' },
  { value: 'impersonation', label: "Se fait passer pour quelqu'un, ou recopie un texte" },
  { value: 'spam', label: 'Publicité, spam, vente de kamas ou de comptes' },
  { value: 'hate', label: 'Propos haineux ou discriminatoires' },
  { value: 'personal_info', label: "Informations personnelles sur quelqu'un" },
  { value: 'explicit', label: 'Contenu sexuel explicite' },
  { value: 'illegal', label: 'Menaces, contenu illégal' },
  { value: 'other', label: 'Autre chose' },
]

type Props = {
  target: ReportIn['target']
  targetId: number
  /** Le contenu est-il le mien ? On ne signale pas le sien. */
  mine: boolean
}

/** Un lien discret qui ouvre un petit formulaire : choisir un motif, préciser si besoin, envoyer. */
function ReportButton({ target, targetId, mine }: Props) {
  const me = useMe()
  const id = useId()
  const [open, setOpen] = useState(false)
  const [reason, setReason] = useState<ReportReason | null>(null)
  const [details, setDetails] = useState('')
  const send = useMutation({ mutationFn: sendReport })
  const error = send.error instanceof ApiError ? send.error : null

  if (!me.data || mine) return null

  function submit(event: FormEvent) {
    event.preventDefault()
    if (!reason) return
    send.mutate({ target, target_id: targetId, reason, details: details.trim() || undefined })
  }

  if (send.isSuccess) {
    return (
      <Notice tone="success">
        <p>{send.data.detail}</p>
      </Notice>
    )
  }

  if (!open) {
    return (
      <button type="button" className={styles.open} onClick={() => setOpen(true)}>
        Signaler
      </button>
    )
  }

  const needsDetails = reason === 'other' && !details.trim()

  return (
    <form className={styles.panel} onSubmit={submit} aria-labelledby={`${id}-titre`}>
      <h2 id={`${id}-titre`} className={styles.title}>
        Signaler {target === 'story' ? 'cette histoire' : 'ce personnage'}
      </h2>
      <p className={styles.hint}>
        L'équipe regarde chaque signalement, d'après la{' '}
        <a href="/moderation" target="_blank" rel="noreferrer">
          charte de modération
        </a>
        . Personne ne saura que c'est toi.
      </p>
      {error && (
        <Notice tone="error">
          <p>{error.status === 422 ? (Object.values(error.fields)[0] ?? error.message) : error.message}</p>
        </Notice>
      )}
      <fieldset className={styles.reasons}>
        <legend className={styles.legend}>Ce qui pose problème</legend>
        {REASONS.map((r) => (
          <label key={r.value} className={styles.reason}>
            <input type="radio" name={`${id}-motif`} value={r.value} checked={reason === r.value} onChange={() => setReason(r.value)} />
            <span>{r.label}</span>
          </label>
        ))}
      </fieldset>
      <label className={styles.details}>
        <span className={styles.legend}>{reason === 'other' ? 'En quelques mots' : 'Préciser, si tu veux'}</span>
        <textarea value={details} onChange={(event) => setDetails(event.target.value)} maxLength={DETAILS_MAX} rows={3} />
      </label>
      <div className={styles.actions}>
        <Button variant="secondary" onClick={() => setOpen(false)}>
          Annuler
        </Button>
        <Button type="submit" busy={send.isPending} disabled={!reason || needsDetails}>
          Envoyer le signalement
        </Button>
      </div>
    </form>
  )
}

export default ReportButton
