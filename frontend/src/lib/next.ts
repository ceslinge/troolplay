/** Où revenir après la connexion : seulement une page du site, jamais une adresse d'ailleurs. */
export function safeNext(value: string | null): string {
  if (!value || !value.startsWith('/') || value.startsWith('//') || value.startsWith('/\\')) return '/'
  return value
}

/** La fiche commencée avant l'inscription attend sur cet appareil : on y ramène après la connexion. */
export const RESUME_SHEET = '/personnages/nouveau?reprise=1'

/** Présenter un personnage sur ce serveur : la création le préremplit (#139). */
export const newSheetOn = (serverId: number) => `/personnages/nouveau?serveur=${serverId}`
