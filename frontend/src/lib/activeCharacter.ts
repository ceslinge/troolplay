import { useQuery } from '@tanstack/react-query'
import { useSyncExternalStore } from 'react'
import { fetchMyCharacters, type MyCharacter } from '../api/characters'
import { ACTIVE_CHARACTER_KEY, readStored, store } from './storage'
import { useMe } from './useMe'

// Le personnage avec lequel on joue en ce moment, retenu sur cet appareil.
const CHANGED = 'troolplay:personnage-actif-change'

function read(): number | null {
  return Number(readStored(ACTIVE_CHARACTER_KEY)) || null
}

export function setActiveCharacter(id: number) {
  store(ACTIVE_CHARACTER_KEY, String(id))
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
