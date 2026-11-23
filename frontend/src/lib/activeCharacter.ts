import { useQuery } from '@tanstack/react-query'
import { useSyncExternalStore } from 'react'
import { fetchMyCharacters, type MyCharacter } from '../api/characters'
import { useMe } from './useMe'

// Le personnage avec lequel on joue en ce moment, retenu sur cet appareil.
const KEY = 'troolplay:personnage-actif'
const CHANGED = 'troolplay:personnage-actif-change'

function read(): number | null {
  try {
    return Number(localStorage.getItem(KEY)) || null
  } catch {
    return null
  }
}

export function setActiveCharacter(id: number) {
  try {
    localStorage.setItem(KEY, String(id))
  } catch {
    // Navigation privée : le choix ne sera pas retenu, rien de grave.
  }
  window.dispatchEvent(new Event(CHANGED))
}

function subscribe(onChange: () => void) {
  window.addEventListener(CHANGED, onChange)
  // Un autre onglet a changé de personnage.
  window.addEventListener('storage', onChange)
  return () => {
    window.removeEventListener(CHANGED, onChange)
    window.removeEventListener('storage', onChange)
  }
}

/** Ses personnages, quand on est connecté. undefined pour un visiteur, ou tant que la liste n'est pas arrivée. */
export function useMyCharacters(): MyCharacter[] | undefined {
  const me = useMe()
  const mine = useQuery({ queryKey: ['characters', 'mine'], queryFn: fetchMyCharacters, enabled: Boolean(me.data) })
  // Après une déconnexion, l'ancienne liste peut rester en mémoire : on ne la montre qu'à son propriétaire.
  if (!me.data) return undefined
  // Liste injoignable : on fait comme si elle était vide, plutôt que d'attendre pour rien.
  return mine.isError ? [] : mine.data
}

/**
 * Le personnage actif : celui choisi dans la barre, ou à défaut le premier.
 * undefined pour un visiteur, ou tant que la liste n'est pas arrivée.
 */
export function useActiveCharacter(): MyCharacter | undefined {
  const mine = useMyCharacters()
  const stored = useSyncExternalStore(subscribe, read, () => null)
  const list = mine ?? []
  return list.find((c) => c.id === stored) ?? list[0]
}
