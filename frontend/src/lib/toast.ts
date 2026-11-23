import { createContext, useContext } from 'react'

export type ToastTone = 'success' | 'error' | 'info'

export type Toast = { id: number; message: string; tone: ToastTone }

export type ToastApi = { show: (message: string, tone?: ToastTone) => void }

export const ToastContext = createContext<ToastApi>({ show: () => {} })

/** Prévenir d'un coup d'œil, en bas de l'écran : « Fiche enregistrée », « Pas enregistré »… */
export function useToast(): ToastApi {
  return useContext(ToastContext)
}

/** Amène la personne au premier champ en erreur, et y met le curseur. */
export function focusFirstError() {
  // On attend que la page affiche les erreurs avant de les chercher.
  setTimeout(() => {
    // Un champ marqué invalide, ou une erreur qui porte sur un groupe (les lieux).
    const field = document.querySelector<HTMLElement>('[aria-invalid="true"], [data-error]')
    field?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    field?.focus({ preventScroll: true })
  }, 0)
}
