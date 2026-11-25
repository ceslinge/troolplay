import Button from './Button'
import styles from './FormActions.module.css'

type Props = {
  /** Le bouton d'envoi : « Envoyer le signalement », « Suspendre »… */
  confirm: string
  onCancel: () => void
  busy: boolean
  disabled?: boolean
  danger?: boolean
}

/** Le pied d'un petit formulaire : Annuler, puis le bouton d'envoi. */
function FormActions({ confirm, onCancel, busy, disabled = false, danger = false }: Props) {
  return (
    <div className={styles.actions}>
      <Button variant="secondary" onClick={onCancel}>
        Annuler
      </Button>
      <Button type="submit" variant={danger ? 'danger' : 'primary'} busy={busy} disabled={disabled}>
        {confirm}
      </Button>
    </div>
  )
}

export default FormActions
