import { type ReactNode, useCallback, useMemo, useState } from 'react'
import { type Toast, ToastContext, type ToastTone } from '../lib/toast'
import Medallion from './Medallion'
import styles from './Toaster.module.css'

const DURATION: Record<ToastTone, number> = { success: 4000, info: 5000, error: 8000 }

/** Affiche les notifications en bas de l'écran. À placer une fois, autour de l'appli. */
function Toaster({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])

  const dismiss = useCallback((id: number) => {
    setToasts((current) => current.filter((toast) => toast.id !== id))
  }, [])

  const show = useCallback(
    (message: string, tone: ToastTone = 'info') => {
      const id = Date.now() + Math.random()
      // Trois au plus : une nouvelle notification pousse la plus ancienne.
      setToasts((current) => [...current.slice(-2), { id, message, tone }])
      setTimeout(() => dismiss(id), DURATION[tone])
    },
    [dismiss],
  )

  const api = useMemo(() => ({ show }), [show])

  return (
    <ToastContext.Provider value={api}>
      {children}
      {/* Toujours présente, pour que les lecteurs d'écran annoncent chaque nouvelle notification. */}
      <div className={styles.stack} aria-live="polite">
        {toasts.map((toast) => (
          <div key={toast.id} className={`${styles.toast} ${styles[toast.tone]}`} role={toast.tone === 'error' ? 'alert' : 'status'}>
            <Medallion icon={toast.tone === 'error' ? 'chain' : 'quill'} tone="dark" />
            <p className={styles.message}>{toast.message}</p>
            <button type="button" className={styles.close} onClick={() => dismiss(toast.id)} aria-label="Fermer">
              ×
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

export default Toaster
