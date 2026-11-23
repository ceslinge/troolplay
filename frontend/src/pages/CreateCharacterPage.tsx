import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { type FormEvent, type ReactNode, useEffect, useState } from 'react'
import { Navigate, useNavigate } from 'react-router'
import { type CharacterClass, createCharacter, type Gender, type NewCharacter, type Period } from '../api/characters'
import { ApiError } from '../api/client'
import { fetchServers, type Server } from '../api/servers'
import Button from '../components/Button'
import Chips, { type ChipOption } from '../components/Chips'
import Field from '../components/Field'
import MultiChips from '../components/MultiChips'
import Notice from '../components/Notice'
import Sheet from '../components/Sheet'
import { CLASS_LABELS } from '../lib/classes'
import { DAY_OPTIONS, PERIOD_OPTIONS } from '../lib/schedule'
import { useMe } from '../lib/useMe'
import { FIELD_TEXTS, STORY_FIELDS, type StoryField } from './characterFields'
import styles from './CreateCharacterPage.module.css'

type Draft = Record<StoryField | 'ooc_note' | 'name' | 'ingame_name' | 'level' | 'server_id', string> & {
  gender: Gender
  class: CharacterClass | ''
  play_days: number[]
  play_periods: Period[]
}

const EMPTY: Draft = {
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

const GENDERS: ChipOption<Gender>[] = [
  { value: 'feminine', label: 'Féminin' },
  { value: 'masculine', label: 'Masculin' },
  { value: 'neutral', label: 'Neutre' },
]

// « On ne perd jamais un texte » : le brouillon vit dans le navigateur jusqu'à l'envoi.
const DRAFT_KEY = 'troolplay:brouillon-personnage'

function loadDraft(): Draft {
  try {
    const saved = localStorage.getItem(DRAFT_KEY)
    return saved ? { ...EMPTY, ...JSON.parse(saved) } : EMPTY
  } catch {
    return EMPTY
  }
}

function saveDraft(draft: Draft) {
  try {
    localStorage.setItem(DRAFT_KEY, JSON.stringify(draft))
  } catch {
    // Navigation privée ou stockage plein : tant pis, le formulaire marche quand même.
  }
}

/** Ce qu'on envoie : les champs vides restent de côté. */
function toRequest(draft: Draft): NewCharacter {
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

/** Les étapes du mode guidé, et les champs que chacune remplit. */
const STEPS: (keyof Draft)[][] = [
  ['name', 'server_id'],
  ['gender'],
  ...STORY_FIELDS.map((field) => [field]),
  ['class', 'level', 'ingame_name', 'play_days', 'play_periods'],
  ['ooc_note'],
]

type Mode = 'guided' | 'free'

function CreateCharacterPage() {
  const me = useMe()
  const servers = useQuery({ queryKey: ['servers'], queryFn: fetchServers })
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const [draft, setDraft] = useState<Draft>(loadDraft)
  const [mode, setMode] = useState<Mode>('guided')
  const [step, setStep] = useState(0)

  useEffect(() => saveDraft(draft), [draft])

  const create = useMutation({
    mutationFn: createCharacter,
    onSuccess: async (character) => {
      localStorage.removeItem(DRAFT_KEY)
      await queryClient.invalidateQueries({ queryKey: ['characters'] })
      navigate(`/personnages/${character.id}`)
    },
    onError: (error) => {
      // En mode guidé, on retourne à la première question qui pose problème.
      if (error instanceof ApiError) {
        const wrong = STEPS.findIndex((fields) => fields.some((f) => f in error.fields || (f === 'class' && 'class' in error.fields)))
        if (wrong >= 0) setStep(wrong)
      }
    },
  })
  const errors = create.error instanceof ApiError ? create.error.fields : {}

  if (me.isPending || servers.isPending) {
    return null
  }
  if (!me.data) {
    return <Navigate to="/connexion?suite=/personnages/nouveau" replace />
  }

  const server: Server | undefined = servers.data?.find((s) => String(s.id) === draft.server_id)

  function set<K extends keyof Draft>(key: K, value: Draft[K]) {
    setDraft((current) => {
      const next = { ...current, [key]: value }
      // Une classe qui n'existe pas dans le jeu du nouveau serveur redevient un mystère.
      if (key === 'server_id') {
        const chosen = servers.data?.find((s) => String(s.id) === value)
        if (next.class && chosen && !chosen.classes.includes(next.class)) next.class = ''
      }
      return next
    })
  }

  function submit(event?: FormEvent) {
    event?.preventDefault()
    create.mutate(toRequest(draft))
  }

  // Chaque morceau du formulaire n'est écrit qu'une fois, et sert aux deux modes.
  const parts: Record<keyof Draft, ReactNode> = {
    name: (
      <Field label="Nom du personnage" name="name" value={draft.name} onChange={(v) => set('name', v)} required maxLength={40} hint="Tel que les autres l'appelleront." error={errors.name} />
    ),
    server_id: (
      <label className={styles.select}>
        <span>Serveur</span>
        <select value={draft.server_id} onChange={(event) => set('server_id', event.target.value)} aria-invalid={errors.server_id ? true : undefined}>
          <option value="">Choisir un serveur</option>
          {servers.data?.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </select>
        {errors.server_id && <span className={styles.error}>{errors.server_id}</span>}
      </label>
    ),
    gender: (
      <div className={styles.stack}>
        <Chips legend="Accords du site" options={GENDERS} value={draft.gender} onChange={(v) => set('gender', v ?? 'neutral')} />
        <p className={styles.hint}>Sert seulement à accorder les textes du site. Les pronoms, tu peux les préciser dans la fiche.</p>
      </div>
    ),
    class: (
      <label className={styles.select}>
        <span>Classe</span>
        <select value={draft.class} onChange={(event) => set('class', event.target.value as CharacterClass | '')}>
          <option value="">Un mystère</option>
          {(server?.classes ?? []).map((c) => (
            <option key={c} value={c}>
              {CLASS_LABELS[c]}
            </option>
          ))}
        </select>
        {errors.class && <span className={styles.error}>{errors.class}</span>}
      </label>
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

  const groups: { title: string; fields: (keyof Draft)[] }[] = [
    { title: 'Qui est-ce ?', fields: ['name', 'server_id', 'gender'] },
    { title: 'En jeu', fields: ['class', 'level', 'ingame_name', 'play_days', 'play_periods'] },
    { title: 'Son histoire', fields: [...STORY_FIELDS] },
    { title: 'Hors RP', fields: ['ooc_note'] },
  ]
  const last = step === STEPS.length - 1
  const firstStepDone = draft.name.trim().length >= 2 && draft.server_id !== ''

  return (
    <main className={styles.page}>
      <div className={styles.top}>
        <h1 className={styles.title}>Épingler un personnage</h1>
        <div className={styles.modes} role="group" aria-label="Façon de remplir">
          <button type="button" aria-pressed={mode === 'guided'} onClick={() => setMode('guided')}>
            Guidé
          </button>
          <button type="button" aria-pressed={mode === 'free'} onClick={() => setMode('free')}>
            Libre
          </button>
        </div>
      </div>
      <p className={styles.lead}>
        Seuls le nom et le serveur sont obligatoires. Ton brouillon est gardé sur cet appareil, tu peux revenir plus tard.
      </p>

      {create.isError && !(create.error instanceof ApiError && create.error.status === 422) && (
        <Notice tone="error">
          <p>{create.error.message}</p>
        </Notice>
      )}

      {mode === 'guided' ? (
        <Sheet seed={`creation-${step}`} as="section" contentClassName={styles.card}>
          <span className={styles.progress}>
            Question {step + 1} sur {STEPS.length}
          </span>
          {step === 0 && <h2 className={styles.question}>Comment s'appelle ce personnage, et où vit-il ?</h2>}
          {step === 1 && <h2 className={styles.question}>Comment le site doit-il parler de ce personnage ?</h2>}
          <div className={styles.stack}>{STEPS[step].map((key) => <div key={key}>{parts[key]}</div>)}</div>
          <div className={styles.nav}>
            {step > 0 && (
              <Button variant="secondary" onClick={() => setStep(step - 1)}>
                Précédent
              </Button>
            )}
            {last ? (
              <Button busy={create.isPending} onClick={() => submit()}>
                Épingler mon personnage
              </Button>
            ) : (
              <>
                {step > 0 && (
                  <button type="button" className={styles.skip} onClick={() => setStep(step + 1)}>
                    Passer
                  </button>
                )}
                <Button onClick={() => setStep(step + 1)}>Suivant</Button>
              </>
            )}
          </div>
          {step > 0 && firstStepDone && !last && (
            <button type="button" className={styles.skip} onClick={() => submit()}>
              Épingler tout de suite, je compléterai plus tard
            </button>
          )}
        </Sheet>
      ) : (
        <form onSubmit={submit} noValidate className={styles.stack}>
          {groups.map((group) => (
            <Sheet key={group.title} seed={`creation-${group.title}`} as="section" contentClassName={styles.card}>
              <h2 className={styles.question}>{group.title}</h2>
              <div className={styles.stack}>{group.fields.map((key) => <div key={key}>{parts[key]}</div>)}</div>
            </Sheet>
          ))}
          <div className={styles.nav}>
            <Button type="submit" busy={create.isPending}>
              Épingler mon personnage
            </Button>
          </div>
        </form>
      )}
    </main>
  )
}

export default CreateCharacterPage
