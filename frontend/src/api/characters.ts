import { apiFetch } from './client'
import type { Server } from './servers'

export type Hangout = {
  id: number
  area: string
  x: number
  y: number
  label: string | null
  habits: string | null
}

export type CharacterClass =
  | 'feca'
  | 'osamodas'
  | 'enutrof'
  | 'sram'
  | 'xelor'
  | 'ecaflip'
  | 'eniripsa'
  | 'iop'
  | 'cra'
  | 'sadida'
  | 'sacrieur'
  | 'pandawa'
  | 'roublard'
  | 'zobal'
  | 'steamer'
  | 'eliotrope'
  | 'huppermage'
  | 'ouginak'
  | 'forgelance'
  | 'bellaphone'

export type Gender = 'feminine' | 'masculine' | 'neutral'

export type Period = 'morning' | 'afternoon' | 'evening' | 'night'

/** Ce qu'une liste montre d'un personnage. */
export type CharacterSummary = {
  id: number
  server: Server | null
  name: string
  gender: Gender
  class: CharacterClass | null
  level: number | null
  avatar: string | null
  seal: string | null
  hook: string | null
  play_days: number[]
  play_periods: Period[]
  inactive: boolean
}

/** La fiche complète : le résumé, et tout le reste. */
export type Character = CharacterSummary & {
  is_npc: boolean
  ingame_name: string | null
  appearance: string | null
  personality: string | null
  backstory: string | null
  goals: string | null
  flaws: string | null
  rumors: string | null
  ooc_note: string | null
  hangouts: Hangout[]
  inactive_note: string | null
  created_at: string
  updated_at: string
  /** Seulement pour le propriétaire (et la modération). */
  is_mine?: boolean
  hidden?: boolean
}

export async function fetchCharacter(id: string): Promise<Character | null> {
  const response = await fetch(`/api/characters/${id}`)
  if (response.status === 404) {
    return null
  }
  if (!response.ok) {
    throw new Error(`Erreur ${response.status}`)
  }
  return response.json()
}

export type DirectoryFilters = {
  serverId: number
  day?: number
  period?: Period
  /** Une partie du nom ou du nom en jeu. */
  q?: string
  includeInactive?: boolean
  page: number
}

export const PAGE_SIZE = 24

export async function fetchCharacters(
  filters: DirectoryFilters,
): Promise<{ items: CharacterSummary[]; total: number }> {
  const params = new URLSearchParams({
    server_id: String(filters.serverId),
    limit: String(PAGE_SIZE),
    offset: String((filters.page - 1) * PAGE_SIZE),
  })
  if (filters.day) params.set('day', String(filters.day))
  if (filters.period) params.set('period', filters.period)
  if (filters.q) params.set('q', filters.q)
  if (filters.includeInactive) params.set('include_inactive', 'true')

  const response = await fetch(`/api/characters?${params}`)
  if (!response.ok) {
    throw new Error(`Erreur ${response.status}`)
  }
  return response.json()
}

/** Ce qu'on envoie pour créer un personnage : seuls le nom et le serveur sont obligatoires. */
export type NewCharacter = {
  name: string
  server_id: number
  gender?: Gender
  class?: CharacterClass
  level?: number
  ingame_name?: string
  hook?: string
  appearance?: string
  personality?: string
  backstory?: string
  goals?: string
  flaws?: string
  rumors?: string
  ooc_note?: string
  play_days?: number[]
  play_periods?: Period[]
}

export const createCharacter = (body: NewCharacter) =>
  apiFetch<Character>('/characters', { method: 'POST', body })

/** Ce qu'on envoie pour modifier : null vide un champ facultatif. */
export type CharacterChanges = {
  name?: string
  server_id?: number
  gender?: Gender
  class?: CharacterClass | null
  level?: number | null
  ingame_name?: string | null
  hook?: string | null
  appearance?: string | null
  personality?: string | null
  backstory?: string | null
  goals?: string | null
  flaws?: string | null
  rumors?: string | null
  ooc_note?: string | null
  play_days?: number[]
  play_periods?: Period[]
  /** Mettre en retrait (true, avec une raison facultative) ou faire revenir (false). */
  inactive?: boolean
  inactive_note?: string | null
}

export const updateCharacter = (id: number, body: CharacterChanges) =>
  apiFetch<Character>(`/characters/${id}`, { method: 'PATCH', body })

export type NewHangout = Omit<Hangout, 'id'>

export const replaceHangouts = (id: number, hangouts: NewHangout[]) =>
  apiFetch<Hangout[]>(`/characters/${id}/hangouts`, { method: 'PUT', body: hangouts })

export const deleteCharacter = (id: number) => apiFetch(`/characters/${id}`, { method: 'DELETE' })

/** Mes personnages, en retrait et masqués compris. */
export type MyCharacter = CharacterSummary & { hidden: boolean; is_mine: boolean }

export async function fetchMyCharacters(): Promise<MyCharacter[]> {
  const body = await apiFetch<{ items: MyCharacter[] }>('/me/characters')
  return body.items
}

/** Ranger ses personnages : tous, dans l'ordre voulu. */
export async function orderMyCharacters(ids: number[]): Promise<MyCharacter[]> {
  const body = await apiFetch<{ items: MyCharacter[] }>('/me/characters/order', { method: 'PUT', body: { ids } })
  return body.items
}

/** Pas plus de personnages par compte (le serveur le vérifie aussi). */
export const MAX_CHARACTERS = 10

