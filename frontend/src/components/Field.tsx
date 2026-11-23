import { useId } from 'react'
import styles from './Field.module.css'

type Props = {
  label: string
  name: string
  type?: 'text' | 'email' | 'password'
  value: string
  onChange: (value: string) => void
  error?: string
  hint?: string
  autoComplete?: string
  required?: boolean
}

/** Un champ de formulaire, son étiquette, son aide et son erreur. */
function Field({ label, name, type = 'text', value, onChange, error, hint, autoComplete, required }: Props) {
  const id = useId()
  const describedBy = [hint && `${id}-aide`, error && `${id}-erreur`].filter(Boolean).join(' ') || undefined
  return (
    <div className={styles.field}>
      <label htmlFor={id} className={styles.label}>
        {label}
      </label>
      <input
        id={id}
        name={name}
        type={type}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        autoComplete={autoComplete}
        required={required}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy}
        className={styles.input}
      />
      {hint && (
        <span id={`${id}-aide`} className={styles.hint}>
          {hint}
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
