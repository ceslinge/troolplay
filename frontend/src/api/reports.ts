import { apiFetch } from './client'

export type ReportReason =
  | 'off_topic'
  | 'disrespect'
  | 'hate'
  | 'explicit'
  | 'personal_info'
  | 'impersonation'
  | 'spam'
  | 'illegal'
  | 'other'

export type ReportIn = {
  target: 'character' | 'story'
  target_id: number
  reason: ReportReason
  details?: string
}

export const DETAILS_MAX = 1000

export const sendReport = (report: ReportIn) => apiFetch<{ detail: string }>('/reports', { method: 'POST', body: report })
