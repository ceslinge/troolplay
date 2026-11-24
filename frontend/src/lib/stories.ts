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

/** « 12 min de lecture », à 230 mots par minute environ. */
export function readingTime(body: string): string {
  const words = body.trim() ? body.trim().split(/\s+/).length : 0
  return `${Math.max(1, Math.round(words / 230))} min de lecture`
}
