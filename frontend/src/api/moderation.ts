import { apiFetch } from './client'
import type { ReportReason } from './reports'

export type Target = 'character' | 'story'
export type Decision = 'founded' | 'no_action' | 'abusive'
export type Duration = 'day' | 'week' | 'month' | 'forever'

export type Reporter = { id: number | null; reports_sent: number; founded: number; abusive: number; reporting_revoked: boolean }

export type Report = {
  id: number
  reason: ReportReason
  details: string | null
  created_at: string
  decision: Decision | null
  handled_at: string | null
  reporter: Reporter
  snapshot: Record<string, unknown> | null
}

export type CaseSummary = {
  target: Target
  target_id: number
  label: string
  exists: boolean
  hidden: boolean
  /** Caché par le masquage automatique, en attendant qu'un modérateur regarde. */
  auto_hidden: boolean
  open_reports: number
  total_reports: number
  reasons: Partial<Record<ReportReason, number>>
  last_reported_at: string
}

export type TeamAccount = {
  id: number
  role: 'user' | 'moderator' | 'admin'
  created_at: string
  verified: boolean
  suspended: boolean
  banned_until: string | null
  reporting_revoked: boolean
  characters: { id: number; name: string; server: string | null; hidden: boolean }[]
  reports_received: number
  reports_sent: number
}

export type CaseDetail = CaseSummary & { owner: TeamAccount | null; reports: Report[] }

export type TeamContent = { target: Target; target_id: number; hidden: boolean; owner: TeamAccount | null; open_reports: number }

export type JournalEntry = {
  id: number
  actor_id: number | null
  action: string
  target_user_id: number | null
  target_character_id: number | null
  target_story_id: number | null
  detail: string | null
  reason: string
  created_at: string
}

const plural = (target: Target) => (target === 'character' ? 'characters' : 'stories')

export const fetchCases = (status: 'open' | 'closed') =>
  apiFetch<{ items: CaseSummary[]; total: number }>(`/moderation/cases?status=${status}`)

export const fetchCase = (target: Target, id: number) => apiFetch<CaseDetail>(`/moderation/cases/${target}/${id}`)

export const decide = (target: Target, id: number, decision: Decision, reason: string) =>
  apiFetch<CaseDetail>(`/moderation/cases/${target}/${id}/decide`, { method: 'POST', body: { decision, reason } })

export const fetchTeamContent = (target: Target, id: number) => apiFetch<TeamContent>(`/moderation/${plural(target)}/${id}`)

export const setHidden = (target: Target, id: number, hidden: boolean, reason: string) =>
  apiFetch<{ detail: string }>(`/moderation/${plural(target)}/${id}/${hidden ? 'hide' : 'unhide'}`, { method: 'POST', body: { reason } })

export const fetchTeamAccount = (id: number) => apiFetch<TeamAccount>(`/moderation/accounts/${id}`)

export const suspend = (id: number, duration: Duration, reason: string) =>
  apiFetch<TeamAccount>(`/moderation/accounts/${id}/suspend`, { method: 'POST', body: { duration, reason } })

export const reinstate = (id: number, reason: string) =>
  apiFetch<TeamAccount>(`/moderation/accounts/${id}/reinstate`, { method: 'POST', body: { reason } })

export const setReporting = (id: number, allowed: boolean, reason: string) =>
  apiFetch<TeamAccount>(`/moderation/accounts/${id}/reporting`, { method: 'POST', body: { allowed, reason } })

export function fetchJournal(filters: { action?: string; actorId?: number; targetUserId?: number; page?: number }) {
  const params = new URLSearchParams({ limit: '50', offset: String(((filters.page ?? 1) - 1) * 50) })
  if (filters.action) params.set('action', filters.action)
  if (filters.actorId) params.set('actor_id', String(filters.actorId))
  if (filters.targetUserId) params.set('target_user_id', String(filters.targetUserId))
  return apiFetch<{ items: JournalEntry[]; total: number }>(`/moderation/journal?${params}`)
}

export type Role = 'user' | 'moderator' | 'admin'

export type TeamMember = { id: number; role: Role; characters: string[]; suspended: boolean }

export const fetchTeam = () => apiFetch<{ items: TeamMember[] }>('/moderation/team').then((r) => r.items)

/** Par son adresse exacte, en POST : une adresse n'a rien à faire dans une URL. */
export const lookupAccount = (email: string) => apiFetch<{ id: number }>('/moderation/accounts/lookup', { method: 'POST', body: { email } })

export const changeRole = (id: number, role: Role, reason: string) =>
  apiFetch<TeamAccount>(`/moderation/accounts/${id}/role`, { method: 'POST', body: { role, reason } })
