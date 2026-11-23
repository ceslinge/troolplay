import type { Gender } from '../api/characters'
import { agree } from '../lib/agree'

/** Les textes RP d'une fiche, dans l'ordre où on les remplit. */
export const STORY_FIELDS = [
  'hook',
  'appearance',
  'personality',
  'backstory',
  'goals',
  'flaws',
  'rumors',
] as const

export type StoryField = (typeof STORY_FIELDS)[number]

type FieldText = {
  /** L'étiquette du mode libre. */
  label: string
  /** La question du mode guidé, accordée au personnage. */
  question: (gender: Gender) => string
  hint?: string
  rows: number
  maxLength: number
}

/** Chaque champ est décrit une fois : les deux modes du formulaire n'en sont que deux affichages. */
export const FIELD_TEXTS: Record<StoryField | 'ooc_note', FieldText> = {
  hook: {
    label: 'Réplique d’accroche',
    question: (g) =>
      agree(g, {
        feminine: 'Que répond-elle quand on l’aborde ?',
        masculine: 'Que répond-il quand on l’aborde ?',
        neutral: 'Que répond ce personnage quand on l’aborde ?',
      }),
    hint: 'Une phrase, comme si on lui parlait en jeu. Elle s’affiche en tête de la fiche.',
    rows: 2,
    maxLength: 200,
  },
  appearance: {
    label: 'Apparence',
    question: (g) =>
      agree(g, {
        feminine: 'À quoi la reconnaît-on ?',
        masculine: 'À quoi le reconnaît-on ?',
        neutral: 'À quoi reconnaît-on ce personnage ?',
      }),
    rows: 3,
    maxLength: 2000,
  },
  personality: {
    label: 'Caractère',
    question: () => 'Comment se comporte ce personnage avec les autres ?',
    rows: 3,
    maxLength: 2000,
  },
  backstory: {
    label: 'Histoire',
    question: (g) =>
      agree(g, { feminine: 'D’où vient-elle ?', masculine: 'D’où vient-il ?', neutral: 'D’où vient ce personnage ?' }),
    hint: 'Ce que les autres pourraient apprendre de son passé.',
    rows: 6,
    maxLength: 10000,
  },
  goals: {
    label: 'Quête',
    question: (g) =>
      agree(g, { feminine: 'Que cherche-t-elle ?', masculine: 'Que cherche-t-il ?', neutral: 'Que cherche ce personnage ?' }),
    rows: 3,
    maxLength: 2000,
  },
  flaws: {
    label: 'Failles',
    question: (g) =>
      agree(g, {
        feminine: 'Qu’est-ce qui la perdra ?',
        masculine: 'Qu’est-ce qui le perdra ?',
        neutral: 'Qu’est-ce qui perdra ce personnage ?',
      }),
    rows: 3,
    maxLength: 2000,
  },
  rumors: {
    label: 'Rumeurs',
    question: () => 'Que raconte-t-on à son sujet, au comptoir ?',
    hint: 'Vraies ou fausses, à toi de voir.',
    rows: 3,
    maxLength: 2000,
  },
  ooc_note: {
    label: 'Un mot hors RP',
    question: () => 'Un mot, hors RP, pour les autres joueurs ?',
    hint: 'Ce que tu aimes jouer, comment t’aborder…',
    rows: 2,
    maxLength: 500,
  },
}
