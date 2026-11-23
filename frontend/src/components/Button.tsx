import type { ReactNode } from 'react'
import styles from './Button.module.css'

type Props = {
  children: ReactNode
  variant?: 'primary' | 'secondary' | 'danger'
  type?: 'button' | 'submit'
  busy?: boolean
  disabled?: boolean
  onClick?: () => void
}

/** Un bouton du site. busy le désactive et le montre occupé pendant une requête. */
function Button({ children, variant = 'primary', type = 'button', busy = false, disabled = false, onClick }: Props) {
  return (
    <button
      type={type}
      className={`${styles.button} ${styles[variant]}`}
      disabled={busy || disabled}
      aria-busy={busy || undefined}
      onClick={onClick}
    >
      {busy ? 'Un instant…' : children}
    </button>
  )
}

export default Button
