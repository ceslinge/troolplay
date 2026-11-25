import type { CharacterClass, CharacterSummary, Period } from './characters'
import { apiFetch } from './client'

export type Server = {
  id: number
  game: 'dofus' | 'retro' | 'touch'
  name: string
  classes: CharacterClass[]
  /** Fermé par l'équipe : ses fiches restent lisibles, on n'en crée plus. */
  closed: boolean
}

export async function fetchServers(): Promise<Server[]> {
  const response = await fetch('/api/servers')
  if (!response.ok) {
    throw new Error(`Erreur ${response.status}`)
  }
  const body: { items: Server[] } = await response.json()
  return body.items
}

export type Regular = { character: CharacterSummary; habits: string | null }

/** Un lieu de prédilection, et ceux qui ont l'habitude d'y être. */
export type Place = { area: string; x: number; y: number; label: string | null; regulars: Regular[] }

export async function fetchPlaces(serverId: number, filters: { day?: number; period?: Period }): Promise<Place[]> {
  const params = new URLSearchParams()
  if (filters.day) params.set('day', String(filters.day))
  if (filters.period) params.set('period', filters.period)
  const body = await apiFetch<{ items: Place[] }>(`/servers/${serverId}/places?${params}`)
  return body.items
}

