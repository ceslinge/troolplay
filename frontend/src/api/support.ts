import { apiFetch } from './client'

// Écrire à l'équipe (#142).
export type Topic = 'question' | 'problem' | 'bug'

export type SupportMessage = { id: number; from_team: boolean; body: string; created_at: string; author_id?: number | null }

export type Conversation = {
  id: number
  topic: Topic
  created_at: string
  updated_at: string
  waiting_for_team: boolean
  closed_at: string | null
  messages: SupportMessage[]
}

export const MESSAGE_MIN = 10
export const MESSAGE_MAX = 4000

export const fetchMyConversations = () => apiFetch<{ items: Conversation[] }>('/me/conversations').then((r) => r.items)

export const startConversation = (topic: Topic, body: string) =>
  apiFetch<Conversation>('/me/conversations', { method: 'POST', body: { topic, body } })

export const replyAsMember = (id: number, body: string) =>
  apiFetch<Conversation>(`/me/conversations/${id}/messages`, { method: 'POST', body: { body } })

export type TeamConversation = Conversation & { user_id: number }
export type Queue = 'waiting' | 'answered' | 'closed'

export const fetchTeamConversations = (status: Queue) =>
  apiFetch<{ items: TeamConversation[]; total: number }>(`/moderation/conversations?status=${status}`)

export const replyAsTeam = (id: number, body: string) =>
  apiFetch<TeamConversation>(`/moderation/conversations/${id}/messages`, { method: 'POST', body: { body } })

export const closeConversation = (id: number) => apiFetch<TeamConversation>(`/moderation/conversations/${id}/close`, { method: 'POST' })
