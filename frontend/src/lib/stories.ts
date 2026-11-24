import type { ChipOption } from '../components/Chips'
import type { ContentWarning } from '../api/stories'

export const WARNING_LABELS: Record<ContentWarning, string> = {
  violence: 'Violence graphique',
  death: 'Mort',
  torture: 'Torture',
  sexual_themes: 'Thèmes sexuels',
  abuse: 'Maltraitance',
  self_harm: 'Suicide, automutilation',
  addiction: 'Addictions',
  phobia: 'Phobies',
}

/** Le texte complet, lu par les lecteurs d'écran, quand le libellé est court. */
const WARNING_TITLES: Partial<Record<ContentWarning, string>> = {
  sexual_themes: 'Thèmes sexuels, sans scène explicite',
  abuse: 'Maltraitance, violences conjugales',
  phobia: 'Phobies : insectes, araignées…',
}

export const WARNING_OPTIONS: ChipOption<ContentWarning>[] = (Object.keys(WARNING_LABELS) as ContentWarning[]).map(
  (value) => ({ value, label: WARNING_LABELS[value], title: WARNING_TITLES[value] }),
)

/** Le temps de lecture d'un texte, à 230 mots par minute, comme le calcule le serveur. */
export function readingMinutes(body: string): number {
  const words = body.trim() ? body.trim().split(/\s+/).length : 0
  return Math.max(1, Math.round(words / 230))
}

export const readingLabel = (minutes: number) => `${minutes} min de lecture`

/** « le 24 novembre », ou avec l'année quand ce n'est pas celle-ci. */
export function storyDate(iso: string): string {
  const date = new Date(iso)
  const sameYear = date.getFullYear() === new Date().getFullYear()
  return date.toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', ...(sameYear ? {} : { year: 'numeric' }) })
}
