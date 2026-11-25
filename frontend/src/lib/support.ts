import type { Conversation, Topic } from '../api/support'

export const TOPIC_LABELS: Record<Topic, string> = { question: 'Une question', problem: 'Un problème', bug: 'Un bug' }

/** Où en est la conversation, vu du membre. */
export function conversationState(c: Conversation): string {
  if (c.closed_at) return 'close'
  return c.waiting_for_team ? 'en attente de l’équipe' : 'l’équipe a répondu'
}
