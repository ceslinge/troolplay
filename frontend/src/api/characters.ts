export type Server = {
  id: number
  game: 'dofus' | 'retro' | 'touch'
  name: string
}

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

export type Character = {
  id: number
  server: Server | null
  is_npc: boolean
  name: string
  gender: Gender
  ingame_name: string | null
  class: CharacterClass | null
  level: number | null
  avatar: string | null
  seal: string | null
  hook: string | null
  appearance: string | null
  personality: string | null
  backstory: string | null
  goals: string | null
  flaws: string | null
  rumors: string | null
  ooc_note: string | null
  play_days: number[]
  play_periods: Period[]
  hangouts: Hangout[]
  inactive: boolean
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
