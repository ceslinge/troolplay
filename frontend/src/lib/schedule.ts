import type { Period } from '../api/characters'
import type { ChipOption } from '../components/Chips'

const DAYS = ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche']

const PERIODS: Record<Period, string> = {
  morning: 'le matin',
  afternoon: "l'après-midi",
  evening: 'le soir',
  night: 'la nuit',
}

const ORDER: Period[] = ['morning', 'afternoon', 'evening', 'night']

function list(words: string[]): string {
  if (words.length <= 1) {
    return words.join('')
  }
  return `${words.slice(0, -1).join(', ')} et ${words.at(-1)}`
}

function days(numbers: number[]): string {
  const sorted = [...numbers].sort((a, b) => a - b)
  const key = sorted.join(',')
  if (key === '1,2,3,4,5,6,7') return 'tous les jours'
  if (key === '1,2,3,4,5') return 'en semaine'
  if (key === '6,7') return 'le week-end'
  return list(sorted.map((day) => DAYS[day - 1]))
}

/** « Le soir, lundi, mercredi et vendredi », ou null si rien n'est indiqué. */
export function formatSchedule(dayNumbers: number[], periods: Period[]): string | null {
  const when = list(ORDER.filter((period) => periods.includes(period)).map((p) => PERIODS[p]))
  const on = dayNumbers.length > 0 ? days(dayNumbers) : ''
  const text = [when, on].filter(Boolean).join(', ')
  return text ? text.charAt(0).toUpperCase() + text.slice(1) : null
}

/** Les jours et les créneaux, prêts pour des boutons de choix. */
export const DAY_OPTIONS: ChipOption<number>[] = [
  { value: 1, label: 'L', title: 'Lundi' },
  { value: 2, label: 'M', title: 'Mardi' },
  { value: 3, label: 'M', title: 'Mercredi' },
  { value: 4, label: 'J', title: 'Jeudi' },
  { value: 5, label: 'V', title: 'Vendredi' },
  { value: 6, label: 'S', title: 'Samedi' },
  { value: 7, label: 'D', title: 'Dimanche' },
]

export const PERIOD_OPTIONS: ChipOption<Period>[] = [
  { value: 'morning', label: 'Matin' },
  { value: 'afternoon', label: 'Après-midi' },
  { value: 'evening', label: 'Soir' },
  { value: 'night', label: 'Nuit' },
]
