import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { type FormEvent, useEffect, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router'
import { createCharacter, MAX_CHARACTERS } from '../api/characters'
import { ApiError } from '../api/client'
import { fetchServers, type Server } from '../api/servers'
import Button from '../components/Button'
import buttons from '../components/Button.module.css'
import Notice from '../components/Notice'
import Sheet from '../components/Sheet'
import Unreachable from '../components/Unreachable'
import { focusFirstError, useToast } from '../lib/toast'
import { agree } from '../lib/agree'
import { RESUME_SHEET } from '../lib/next'
import { useMe } from '../lib/useMe'
import { STORY_FIELDS } from './characterFields'
import {
  type Draft,
  formParts,
  dropDraft,
  loadDraft,
  type Mode,
  saveDraft,
  toCreateRequest,
  withChange,
} from './characterForm'
import { setActiveCharacter, useMyCharacters } from '../lib/activeCharacter'
import PageTitle from '../components/PageTitle'
import styles from './CreateCharacterPage.module.css'
import { useNamesakes } from '../lib/useNamesakes'
import { ofName } from '../lib/text'

/**
 * Les étapes du mode guidé, et les champs que chacune remplit. L'essentiel d'abord (qui, où,
 * quelle classe), l'histoire ensuite. Les questions d'histoire portent leur titre dans leur champ.
 */
const STEPS: { title?: string; fields: (keyof Draft)[] }[] = [
  { title: "Comment s'appelle ce personnage, et sur quel serveur ?", fields: ['name', 'server_id'] },
  { title: 'Comment le site doit-il parler de ce personnage ?', fields: ['gender'] },
  { title: 'Et en jeu ?', fields: ['class', 'level', 'ingame_name', 'play_days', 'play_periods'] },
  ...STORY_FIELDS.map((field) => ({ fields: [field] })),
  { fields: ['ooc_note'] },
]

function CreateCharacterPage() {
  const me = useMe()
  const mine = useMyCharacters()
  const servers = useQuery({ queryKey: ['servers'], queryFn: fetchServers })
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const [draft, setDraft] = useState<Draft>(loadDraft)
  const [mode, setMode] = useState<Mode>('guided')
  const [step, setStep] = useState(0)
  // Sans compte, « Épingler » invite à s'inscrire : la fiche attend sur cet appareil (#124).
  const [inviting, setInviting] = useState(false)
  const [params] = useSearchParams()
  const toast = useToast()

  useEffect(() => saveDraft(draft), [draft])

  const create = useMutation({
    mutationFn: createCharacter,
    onSuccess: async (character) => {
      dropDraft()
      // Le nouveau venu devient le personnage actif.
      setActiveCharacter(character.id)
      await queryClient.invalidateQueries({ queryKey: ['characters'] })
      await queryClient.invalidateQueries({ queryKey: ['home'] })
      toast.show(`${character.name} est sur le panneau !`, 'success')
      navigate(`/personnages/${character.id}`)
    },
    onError: (error) => {
      const onField = error instanceof ApiError && Object.keys(error.fields).length > 0
      toast.show(onField ? 'Pas encore épinglé : un champ est à corriger.' : `Pas encore épinglé : ${error.message}`, 'error')
      // En mode guidé, on retourne à la première question qui pose problème.
      if (onField) {
        const wrong = STEPS.findIndex(({ fields }) => fields.some((f) => f in error.fields || (f === 'class' && 'class' in error.fields)))
        if (wrong >= 0) setStep(wrong)
        focusFirstError()
      }
    },
  })
  const errors = create.error instanceof ApiError ? create.error.fields : {}

  // Avant les retours anticipés : un hook s'appelle à chaque rendu (#122).
  const namesakes = useNamesakes(draft.server_id, draft.name, draft.ingame_name)

  if (me.isError || servers.isError) {
    return <Unreachable />
  }
  if (me.isPending || servers.isPending) {
    return null
  }
  const server: Server | undefined = servers.data?.find((s) => String(s.id) === draft.server_id)

  function set<K extends keyof Draft>(key: K, value: Draft[K]) {
    setDraft((current) => withChange(current, key, value, servers.data ?? []))
  }

  function submit(event?: FormEvent) {
    event?.preventDefault()
    if (me.data) {
      create.mutate(toCreateRequest(draft))
      return
    }
    // Un visiteur : on vérifie l'essentiel ici, puis on l'invite à créer son compte.
    if (!firstStepDone) {
      setStep(0)
      toast.show('Il manque encore le nom ou le serveur.', 'error')
      return
    }
    setInviting(true)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const parts = formParts({ draft, set, errors, servers: servers.data ?? [], server, mode, namesakes })

  const groups: { title: string; fields: (keyof Draft)[] }[] = [
    { title: 'Qui est-ce ?', fields: ['name', 'server_id', 'gender'] },
    { title: 'En jeu', fields: ['class', 'level', 'ingame_name', 'play_days', 'play_periods'] },
    { title: 'Son histoire', fields: [...STORY_FIELDS] },
    { title: 'Hors RP', fields: ['ooc_note'] },
  ]
  const last = step === STEPS.length - 1
  const firstStepDone = draft.name.trim().length >= 2 && draft.server_id !== ''

  // On attend de savoir combien de personnages on a, pour ne pas faire écrire une fiche refusée à la fin.
  if (me.data && mine === undefined) {
    return null
  }
  if (mine && mine.length >= MAX_CHARACTERS) {
    return (
      <main className={styles.page}>
        <PageTitle>Présenter un nouveau personnage</PageTitle>
        <h1 className={styles.title}>Présenter un nouveau personnage</h1>
        <Notice>
          <p>
            Tu ne peux pas présenter de nouveau personnage : un compte peut en avoir {MAX_CHARACTERS} au plus. Pour faire de la
            place, retire une fiche dont tu ne te sers plus, depuis <Link to="/compte">ton compte</Link>. Mettre un
            personnage en retrait ne libère pas de place.
          </p>
          {draft.name.trim() && (
            <p>
              Ta fiche « {draft.name.trim()} » t'attend sur cet appareil : une fois la place faite, reviens ici pour
              l'épingler.
            </p>
          )}
        </Notice>
      </main>
    )
  }

  return (
    <main className={styles.page}>
      <PageTitle>Présenter un nouveau personnage</PageTitle>
      <div className={styles.top}>
        <h1 className={styles.title}>Présenter un nouveau personnage</h1>
      </div>
      <p className={styles.lead}>
        {me.data
          ? 'Seuls le nom et le serveur sont obligatoires. Ton brouillon est gardé sur cet appareil, tu peux revenir plus tard.'
          : "Pas besoin de compte pour commencer : ta fiche est gardée sur cet appareil. Seuls le nom et le serveur sont obligatoires."}
      </p>
      {me.data && params.get('reprise') && draft.name.trim() && (
        <Notice tone="success">
          <p>Ta fiche t'attendait. Relis-la si tu veux, puis épingle-la.</p>
        </Notice>
      )}
      {inviting && !me.data && (
        <Sheet seed="creation-invitation" as="section" contentClassName={styles.invite}>
          <h2 className={styles.question}>
            {agree(draft.gender, {
              feminine: `${draft.name.trim()} est prête à être épinglée`,
              masculine: `${draft.name.trim()} est prêt à être épinglé`,
              neutral: `La fiche ${ofName(draft.name.trim())} est prête à être épinglée`,
            })}
          </h2>
          <p>
            Crée ton compte pour l'épingler : ta fiche t'attend sur cet appareil. Après avoir vérifié ton adresse, reviens
            ici, et elle sera sur le panneau en un clic.
          </p>
          <div className={styles.nav}>
            <Link to={`/connexion?suite=${encodeURIComponent(RESUME_SHEET)}`} className={`${buttons.button} ${buttons.secondary}`}>
              J'ai déjà un compte
            </Link>
            <Link to="/inscription" className={`${buttons.button} ${buttons.primary}`}>
              Créer mon compte
            </Link>
          </div>
        </Sheet>
      )}
      {/* Une question à la fois par défaut : un nouveau venu n'a pas à choisir avant d'avoir commencé. */}
      <button type="button" className={`action-link ${styles.switch}`} onClick={() => setMode(mode === 'guided' ? 'free' : 'guided')}>
        {mode === 'guided' ? "Je préfère tout voir d'un coup" : 'Revenir aux questions une à une'}
      </button>

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
          {STEPS[step].title && <h2 className={styles.question}>{STEPS[step].title}</h2>}
          <div className={styles.stack}>{STEPS[step].fields.map((key) => <div key={key}>{parts[key]}</div>)}</div>
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
                  <button type="button" className={`action-link ${styles.skip}`} onClick={() => setStep(step + 1)}>
                    Passer
                  </button>
                )}
                <Button onClick={() => setStep(step + 1)}>Suivant</Button>
              </>
            )}
          </div>
          {step > 0 && firstStepDone && !last && (
            <button type="button" className={`action-link ${styles.skip}`} onClick={() => submit()}>
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
