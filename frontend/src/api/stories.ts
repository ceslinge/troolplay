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
  excerpt: string | null
}

export type MyStorySummary = StorySummary & { updated_at: string; published: boolean; hidden: boolean }

export type StoryFields = {
  character_id: number
  title: string
  body: string
  content_warnings: ContentWarning[]
  content_note: string | null
}

// Les limites du serveur (docs/api.md, « Les histoires »).
export const TITLE_MAX = 120
export const BODY_MAX = 50_000
export const NOTE_MAX = 200
export const MAX_DRAFTS = 30

export const fetchStory = (id: number) => apiFetch<Story>(`/stories/${id}`)

export const fetchMyStories = () => apiFetch<{ items: MyStorySummary[] }>('/me/stories').then((r) => r.items)

export const createStory = (fields: StoryFields) => apiFetch<Story>('/stories', { method: 'POST', body: fields })

export const updateStory = (id: number, fields: Partial<StoryFields>) =>
  apiFetch<Story>(`/stories/${id}`, { method: 'PATCH', body: fields })

export const publishStory = (id: number) => apiFetch<Story>(`/stories/${id}/publish`, { method: 'POST' })

export const unpublishStory = (id: number) => apiFetch<Story>(`/stories/${id}/unpublish`, { method: 'POST' })

export const deleteStory = (id: number) => apiFetch<void>(`/stories/${id}`, { method: 'DELETE' })
