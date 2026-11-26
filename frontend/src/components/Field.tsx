import { type ChangeEvent, useId } from 'react'
import styles from './Field.module.css'

type Props = {
  label: string
  name: string
  type?: 'text' | 'email' | 'password'
  value: string
  onChange: (value: string) => void
  error?: string
  hint?: string
  /** À savoir, sans bloquer l'envoi : un nom déjà porté (#122). Lu par les lecteurs d'écran. */
  warning?: string
  autoComplete?: string
  required?: boolean
  /** Un texte sur plusieurs lignes, avec ce nombre de lignes visibles. */
  rows?: number
  maxLength?: number
}

/** Un champ de formulaire, son étiquette, son aide, un avertissement éventuel et son erreur. */
function Field({
  label,
  name,
  type = 'text',
  value,
  onChange,
  error,
  hint,
  warning,
  autoComplete,
  required,
  rows,
  maxLength,
}: Props) {
  const id = useId()
  const describedBy = [hint && `${id}-aide`, warning && `${id}-attention`, error && `${id}-erreur`].filter(Boolean).join(' ') || undefined
  // Ce que le champ a en commun, sur une ligne ou sur plusieurs.
  const common = {
    id,
    name,
    value,
    onChange: (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => onChange(event.target.value),
    required,
    maxLength,
    'aria-invalid': error ? true : undefined,
    'aria-describedby': describedBy,
  }
  return (
    <div className={styles.field}>
      <label htmlFor={id} className={styles.label}>
        {label}
      </label>
      {rows ? (
        <textarea {...common} rows={rows} className={`${styles.input} ${styles.textarea}`} />
      ) : (
        <input {...common} type={type} autoComplete={autoComplete} className={styles.input} />
      )}
      {hint && (
        <span id={`${id}-aide`} className={styles.hint}>
          {hint}
        </span>
      )}
      {warning && (
        <span id={`${id}-attention`} className={styles.warning} role="status">
          {warning}
        </span>
      )}
      {error && (
        <span id={`${id}-erreur`} className={styles.error}>
          {error}
        </span>
      )}
    </div>
  )
}

export default Field
