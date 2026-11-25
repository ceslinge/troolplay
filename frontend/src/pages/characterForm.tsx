import type { ReactNode } from 'react'
import type { Character, CharacterChanges, CharacterClass, Gender, NewCharacter, Period } from '../api/characters'
import type { Server } from '../api/servers'
import Chips, { type ChipOption } from '../components/Chips'
import Field from '../components/Field'
import Menu from '../components/Menu'
import MultiChips from '../components/MultiChips'
import { CLASS_LABELS } from '../lib/classes'
import { DAY_OPTIONS, PERIOD_OPTIONS } from '../lib/schedule'
import { FIELD_TEXTS, STORY_FIELDS, type StoryField } from './characterFields'
import { serverOptions } from '../lib/games'
import { CHARACTER_DRAFT_KEY, forget, readStored, store } from '../lib/storage'
import styles from './CreateCharacterPage.module.css'

/** Ce que partagent la création et la modification d'une fiche. */

export type Draft = Record<StoryField | 'ooc_note' | 'name' | 'ingame_name' | 'level' | 'server_id', string> & {
  gender: Gender
  class: CharacterClass | ''
  play_days: number[]
  play_periods: Period[]
}

export const EMPTY: Draft = {
  name: '',
  server_id: '',
  gender: 'neutral',
  class: '',
  level: '',
  ingame_name: '',
  hook: '',
  appearance: '',
  personality: '',
  backstory: '',
  goals: '',
  flaws: '',
  rumors: '',
  ooc_note: '',
  play_days: [],
  play_periods: [],
}

export const GENDERS: ChipOption<Gender>[] = [
  { value: 'feminine', label: 'Féminin' },
  { value: 'masculine', label: 'Masculin' },
  { value: 'neutral', label: 'Neutre' },
]

// « On ne perd jamais un texte » : le brouillon vit dans le navigateur jusqu'à l'envoi.
export function loadDraft(): Draft {
  try {
    const saved = readStored(CHARACTER_DRAFT_KEY)
    return saved ? { ...EMPTY, ...JSON.parse(saved) } : EMPTY
  } catch {
    return EMPTY
  }
}

/** Le nom de la fiche commencée sur cet appareil sans être épinglée, ou null. */
export function pendingDraftName(): string | null {
  return loadDraft().name.trim() || null
}

export function hasPendingDraft(): boolean {
  return pendingDraftName() !== null
}

export const saveDraft = (draft: Draft) => store(CHARACTER_DRAFT_KEY, JSON.stringify(draft))

export const dropDraft = () => forget(CHARACTER_DRAFT_KEY)

/** Ce qu'on envoie pour créer : les champs vides restent de côté. */
export function toCreateRequest(draft: Draft): NewCharacter {
  const body: NewCharacter = { name: draft.name.trim(), server_id: Number(draft.server_id), gender: draft.gender }
  if (draft.class) body.class = draft.class
  if (draft.level) body.level = Number(draft.level)
  if (draft.play_days.length) body.play_days = draft.play_days
  if (draft.play_periods.length) body.play_periods = draft.play_periods
  for (const key of ['ingame_name', 'ooc_note', ...STORY_FIELDS] as const) {
    const text = draft[key].trim()
    if (text) body[key] = text
  }
  return body
}

/** Ce qu'on envoie pour modifier : tout, et null pour ce qui a été vidé. */
export function toUpdateRequest(draft: Draft): CharacterChanges {
  const text = (value: string) => value.trim() || null
  return {
    name: draft.name.trim(),
    gender: draft.gender,
    class: draft.class || null,
    level: draft.level ? Number(draft.level) : null,
    play_days: draft.play_days,
    play_periods: draft.play_periods,
    ingame_name: text(draft.ingame_name),
    ooc_note: text(draft.ooc_note),
    ...Object.fromEntries(STORY_FIELDS.map((key) => [key, text(draft[key])])),
  }
}

/** Le brouillon de départ, quand on modifie une fiche existante. */
export function fromCharacter(c: Character): Draft {
  const text = (value: string | null) => value ?? ''
  return {
    name: c.name,
    server_id: c.server ? String(c.server.id) : '',
    gender: c.gender,
    class: c.class ?? '',
    level: c.level ? String(c.level) : '',
    ingame_name: text(c.ingame_name),
    ooc_note: text(c.ooc_note),
    play_days: c.play_days,
    play_periods: c.play_periods,
    hook: text(c.hook),
    appearance: text(c.appearance),
    personality: text(c.personality),
    backstory: text(c.backstory),
    goals: text(c.goals),
    flaws: text(c.flaws),
    rumors: text(c.rumors),
  }
}

/** Applique un changement, avec ses règles : une classe absente du nouveau serveur redevient un mystère. */
export function withChange<K extends keyof Draft>(draft: Draft, key: K, value: Draft[K], servers: Server[]): Draft {
  const next = { ...draft, [key]: value }
  if (key === 'server_id') {
    const chosen = servers.find((s) => String(s.id) === value)
    if (next.class && chosen && !chosen.classes.includes(next.class)) next.class = ''
  }
  return next
}

export type Mode = 'guided' | 'free'

type PartsProps = {
  draft: Draft
  set: <K extends keyof Draft>(key: K, value: Draft[K]) => void
  errors: Record<string, string>
  servers: Server[]
  server: Server | undefined
  mode: Mode
}

/** Chaque morceau du formulaire n'est écrit qu'une fois, et sert aux deux pages et aux deux modes. */
export function formParts({ draft, set, errors, servers, server, mode }: PartsProps): Record<keyof Draft, ReactNode> {
  return {
    name: (
      <Field label="Nom du personnage" name="name" value={draft.name} onChange={(v) => set('name', v)} required maxLength={40} hint="Tel que les autres l'appelleront." error={errors.name} />
    ),
    server_id: (
      // Pas d'option « aucun serveur » : avant le premier choix, le bouton invite simplement à choisir.
      <Menu
        label="Serveur"
        value={draft.server_id}
        options={serverOptions(servers, (s) => String(s.id))}
        onChange={(v) => set('server_id', v)}
        placeholder="Choisir un serveur"
        error={errors.server_id}
      />
    ),
    gender: (
      <div className={styles.stack}>
        <Chips legend="Accords du site" options={GENDERS} value={draft.gender} onChange={(v) => set('gender', v ?? 'neutral')} />
        <p className={styles.hint}>Sert seulement à accorder les textes du site.</p>
      </div>
    ),
    class: (
      <Menu<CharacterClass | ''>
        label="Classe"
        value={draft.class}
        options={[{ value: '', label: 'Un mystère' }, ...(server?.classes ?? []).map((c) => ({ value: c, label: CLASS_LABELS[c] }))]}
        onChange={(v) => set('class', v)}
        error={errors.class}
      />
    ),
    level: (
      <Field label="Niveau" name="level" value={draft.level} onChange={(v) => set('level', v.replace(/\D/g, ''))} hint="Facultatif." error={errors.level} />
    ),
    ingame_name: (
      <Field label="Nom en jeu" name="ingame_name" value={draft.ingame_name} onChange={(v) => set('ingame_name', v)} maxLength={40} hint="Pour le retrouver : les autres pourront le copier." error={errors.ingame_name} />
    ),
    play_days: <MultiChips legend="Joue plutôt le" options={DAY_OPTIONS} value={draft.play_days} onChange={(v) => set('play_days', v)} />,
    play_periods: <MultiChips legend="Plutôt" options={PERIOD_OPTIONS} value={draft.play_periods} onChange={(v) => set('play_periods', v)} />,
    ...Object.fromEntries(
      (['ooc_note', ...STORY_FIELDS] as const).map((key) => {
        const text = FIELD_TEXTS[key]
        return [
          key,
          <Field
            key={key}
            label={mode === 'guided' ? text.question(draft.gender) : text.label}
            name={key}
            value={draft[key]}
            onChange={(v) => set(key, v)}
            rows={text.rows}
            maxLength={text.maxLength}
            hint={text.hint}
            error={errors[key]}
          />,
        ]
      }),
    ),
  } as Record<keyof Draft, ReactNode>
}
