import type { CharacterClass, Gender } from './characters'
import { apiFetch } from './client'
import type { Server } from './servers'

export type ContentWarning =
  | 'violence'
  | 'death'
  | 'torture'
  | 'sexual_themes'
  | 'abuse'
  | 'self_harm'
  | 'addiction'
  | 'phobia'

/** Le personnage qui signe, tel qu'une histoire le présente. */
export type StoryCharacter = {
  id: number
  name: string
  gender: Gender
  class: CharacterClass | null
  avatar: string | null
  seal: string | null
  server: Server | null
}

/** L'histoire complète. hidden n'arrive que pour son auteur et la modération. */
export type Story = {
  id: number
  title: string
  body: string
  character: StoryCharacter | null
  content_warnings: ContentWarning[]
  content_note: string | null
  author_note: string | null
  published: boolean
  published_at: string | null
  updated_at: string
  is_mine: boolean
  hidden?: boolean
}

export type StorySummary = {
  id: number
  title: string
  character: StoryCharacter | null
  content_warnings: ContentWarning[]
  content_note: string | null
  published_at: string | null
  reading_minutes: number
  excerpt: string | null
}

export type StoryOrder = 'newest' | 'oldest'

export type StoryFilters = { serverId?: number; characterId?: number; page?: number; order?: StoryOrder }

export const STORIES_PAGE_SIZE = 20

export type MyStorySummary = StorySummary & { updated_at: string; published: boolean; hidden: boolean }

export type StoryFields = {
  character_id: number
  title: string
  body: string
  content_warnings: ContentWarning[]
  content_note: string | null
  author_note: string | null
}

// Les limites du serveur (docs/api.md, « Les histoires »).
export const TITLE_MAX = 120
export const BODY_MAX = 50_000
export const NOTE_MAX = 200
export const AUTHOR_NOTE_MAX = 1000
/** En dessous, on demande confirmation avant de publier : un mystère tient en une ligne, un « test » aussi. */
export const SHORT_STORY = 200
export const MAX_DRAFTS = 30

export const fetchStory = (id: number) => apiFetch<Story>(`/stories/${id}`)

/** Les histoires publiées d'un serveur, ou d'un personnage, les plus récentes d'abord. */
export function fetchStories(
  { serverId, characterId, page = 1, order }: StoryFilters,
  pageSize = STORIES_PAGE_SIZE,
  offset = (page - 1) * pageSize,
) {
  const params = new URLSearchParams({ limit: String(pageSize), offset: String(offset) })
  if (serverId !== undefined) params.set('server_id', String(serverId))
  if (characterId !== undefined) params.set('character_id', String(characterId))
  if (order) params.set('order', order)
  return apiFetch<{ items: StorySummary[]; total: number }>(`/stories?${params}`)
}

export const fetchMyStories = () => apiFetch<{ items: MyStorySummary[] }>('/me/stories').then((r) => r.items)

export const createStory = (fields: StoryFields) => apiFetch<Story>('/stories', { method: 'POST', body: fields })

export const updateStory = (id: number, fields: Partial<StoryFields>) =>
  apiFetch<Story>(`/stories/${id}`, { method: 'PATCH', body: fields })

export const publishStory = (id: number) => apiFetch<Story>(`/stories/${id}/publish`, { method: 'POST' })

export const unpublishStory = (id: number) => apiFetch<Story>(`/stories/${id}/unpublish`, { method: 'POST' })

export const deleteStory = (id: number) => apiFetch<void>(`/stories/${id}`, { method: 'DELETE' })
