// Ce que le site garde dans le navigateur. Toutes les clés sont ici : rien n'est oublié à la déconnexion.

export const CHARACTER_DRAFT_KEY = 'troolplay:brouillon-personnage'
export const ACTIVE_CHARACTER_KEY = 'troolplay:personnage-actif'
export const HOME_SERVER_KEY = 'troolplay:serveur-accueil'
const STORY_BACKUP_PREFIX = 'troolplay:histoire:'

/** La copie de secours d'une histoire, ou d'une nouvelle histoire pas encore enregistrée. */
export const storyBackupKey = (id: number | null) => `${STORY_BACKUP_PREFIX}${id ?? 'nouvelle'}`

// Navigation privée, stockage bloqué ou plein : le site marche quand même, il retient juste moins.

export function readStored(key: string): string | null {
  try {
    return localStorage.getItem(key)
  } catch {
    return null
  }
}

export function store(key: string, value: string) {
  try {
    localStorage.setItem(key, value)
  } catch {
    // Le choix vaut pour cette visite seulement.
  }
}

export function forget(key: string) {
  try {
    localStorage.removeItem(key)
  } catch {
    // Rien à effacer.
  }
}

/** À la déconnexion : la personne qui prend l'appareil ensuite ne retrouve rien de ce qu'on écrivait. */
export function clearLocalDrafts() {
  try {
    const keys = Array.from({ length: localStorage.length }, (_, i) => localStorage.key(i))
    for (const key of keys) {
      if (key === CHARACTER_DRAFT_KEY || key === ACTIVE_CHARACTER_KEY || key?.startsWith(STORY_BACKUP_PREFIX)) {
        localStorage.removeItem(key)
      }
    }
  } catch {
    // Stockage inaccessible : il n'y avait rien à effacer.
  }
}
