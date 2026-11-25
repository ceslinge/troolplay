import type { Decision, Duration } from '../api/moderation'
import type { ReportReason } from '../api/reports'

export const REASON_LABELS: Record<ReportReason, string> = {
  off_topic: 'Hors sujet',
  disrespect: 'Manque de respect',
  impersonation: 'Usurpation, texte recopié',
  spam: 'Spam, publicité',
  hate: 'Haine, discrimination',
  personal_info: 'Informations personnelles',
  explicit: 'Contenu explicite',
  illegal: 'Menaces, illégal',
  other: 'Autre',
}

export const DECISION_LABELS: Record<Decision, string> = {
  founded: 'Fondé',
  no_action: 'Sans suite',
  abusive: 'Abusif',
}

/** Ce que chaque décision veut dire, pour qu'un nouveau modérateur tranche sans hésiter. */
export const DECISION_HINTS: Record<Decision, string> = {
  founded: "Le signalement était juste. Pense à masquer le contenu s'il ne l'est pas déjà.",
  no_action: 'Rien de contraire aux règles, mais le signalement était de bonne foi.',
  abusive: 'Signalé pour nuire, ou sans aucun motif : cela compte contre son auteur.',
}

export const DURATION_LABELS: Record<Duration, string> = {
  day: '1 jour',
  week: '7 jours',
  month: '30 jours',
  forever: 'Définitivement',
}

export const ACTION_LABELS: Record<string, string> = {
  decide: 'Dossier tranché',
  hide: 'Masqué',
  unhide: 'Rétabli',
  suspend: 'Compte suspendu',
  reinstate: 'Suspension levée',
  revoke_reporting: 'Droit de signaler retiré',
  restore_reporting: 'Droit de signaler rendu',
  set_role: 'Rôle changé',
  auto_hide: 'Masqué automatiquement',
  add_server: 'Serveur ajouté',
  rename_server: 'Serveur renommé',
  close_server: 'Serveur fermé',
  reopen_server: 'Serveur rouvert',
}

export const ROLE_LABELS = { user: 'Joueur', moderator: 'Modérateur', admin: 'Admin' } as const

export function teamDate(iso: string): string {
  return new Date(iso).toLocaleString('fr-FR', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
}

/** Ce que garde une ligne du journal : une décision ou une durée, en clair. */
export function detailLabel(detail: string | null): string | null {
  if (!detail) return null
  return (
    (DECISION_LABELS as Record<string, string>)[detail] ??
    (DURATION_LABELS as Record<string, string>)[detail] ??
    (ROLE_LABELS as Record<string, string>)[detail] ??
    detail
  )
}

/** Qui a agi : un compte de l'équipe, ou le masquage automatique. */
export const actorLabel = (actorId: number | null, action: string) =>
  action === 'auto_hide' ? 'automatiquement' : `par le compte n°${actorId ?? '?'}`
