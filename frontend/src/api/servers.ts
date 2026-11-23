import type { CharacterClass } from './characters'

export type Server = {
  id: number
  game: 'dofus' | 'retro' | 'touch'
  name: string
  classes: CharacterClass[]
}

export async function fetchServers(): Promise<Server[]> {
  const response = await fetch('/api/servers')
  if (!response.ok) {
    throw new Error(`Erreur ${response.status}`)
  }
  const body: { items: Server[] } = await response.json()
  return body.items
}
