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
  characterClass?: CharacterClass
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
  if (filters.characterClass) params.set('class', filters.characterClass)
  if (filters.includeInactive) params.set('include_inactive', 'true')

  const response = await fetch(`/api/characters?${params}`)
  if (!response.ok) {
    throw new Error(`Erreur ${response.status}`)
  }
  return response.json()
}
