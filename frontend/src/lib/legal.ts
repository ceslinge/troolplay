/** Les pages légales et leur adresse sur le site. Le texte vit dans docs/legal, seule source. */
export const LEGAL_PAGES = {
  regles: { path: '/regles', label: "Règles d'usage" },
  moderation: { path: '/moderation', label: 'Charte de modération' },
  confidentialite: { path: '/confidentialite', label: 'Confidentialité' },
  'mentions-legales': { path: '/mentions-legales', label: 'Mentions légales' },
} as const

export type LegalPageName = keyof typeof LEGAL_PAGES
