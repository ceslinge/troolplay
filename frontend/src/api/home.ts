import type { CharacterSummary, Period } from './characters'
import { apiFetch } from './client'
import type { Server } from './servers'

export type RightNow = {
  server: Server
  day: number
  period: Period
  count: number
  places: string[]
}

export type Overheard = {
  character_id: number
  name: string
  server: string | null
  hook: string
}

export type Home = {
  right_now: RightNow | null
  overheard: Overheard | null
  recent: CharacterSummary[]
}

export const fetchHome = (serverId?: number) => apiFetch<Home>(serverId ? `/home?server_id=${serverId}` : '/home')

export const fetchOverheard = () => apiFetch<Overheard | null>('/home/overheard')
