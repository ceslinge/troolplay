import { DRAFT_KEY } from '../pages/characterForm'

// Ce que le site garde sur cet appareil pour la personne connectée.
const ACTIVE_CHARACTER_KEY = 'troolplay:personnage-actif'
const STORY_BACKUP_PREFIX = 'troolplay:histoire:'

/** À la déconnexion : la personne qui prend l'appareil ensuite ne doit rien retrouver de ce qu'on écrivait. */
export function clearLocalDrafts() {
  try {
    const keys = Array.from({ length: localStorage.length }, (_, i) => localStorage.key(i))
    for (const key of keys) {
      if (key === DRAFT_KEY || key === ACTIVE_CHARACTER_KEY || key?.startsWith(STORY_BACKUP_PREFIX)) {
        localStorage.removeItem(key)
      }
    }
  } catch {
    // Stockage inaccessible : il n'y avait rien à effacer.
  }
}
