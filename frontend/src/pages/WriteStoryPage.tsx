import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { type KeyboardEvent, type ReactNode, useEffect, useRef, useState } from 'react'
import { Link, Navigate, useLocation, useNavigate, useParams } from 'react-router'
import type { MyCharacter } from '../api/characters'
import { ApiError } from '../api/client'
import {
  BODY_MAX,
  type ContentWarning,
  createStory,
  deleteStory,
  fetchStory,
  NOTE_MAX,
  publishStory,
  type Story,
  type StoryFields,
  TITLE_MAX,
  unpublishStory,
  updateStory,
} from '../api/stories'
import Button from '../components/Button'
import Field from '../components/Field'
import Menu from '../components/Menu'
import MultiChips from '../components/MultiChips'
import Notice from '../components/Notice'
import PageTitle from '../components/PageTitle'
import Sheet from '../components/Sheet'
import StoryText from '../components/StoryText'
import Unreachable from '../components/Unreachable'
import { useActiveCharacter, useMyCharacters } from '../lib/activeCharacter'
import { WARNING_OPTIONS } from '../lib/stories'
import { useToast } from '../lib/toast'
import { useMe } from '../lib/useMe'
import styles from './WriteStoryPage.module.css'

type Draft = {
  character_id: number
  title: string
  body: string
  content_warnings: ContentWarning[]
  content_note: string
}

// Ce qui se passe en ce moment. « Pas encore enregistré » se déduit : le texte diffère du dernier envoi.
type Activity = 'idle' | 'saving' | 'error'
type Status = 'saved' | 'unsaved' | 'saving' | 'error'

// Un brouillon s'enregistre seul, un peu après la dernière frappe.
const AUTOSAVE_DELAY = 1500
const UNTITLED = 'Sans titre'

function fromStory(story: Story): Draft {
  return {
    character_id: story.character?.id ?? 0,
    title: story.title === UNTITLED ? '' : story.title,
    body: story.body,
    content_warnings: story.content_warnings,
    content_note: story.content_note ?? '',
  }
}

function toFields(draft: Draft): StoryFields {
  return {
    character_id: draft.character_id,
    title: draft.title.trim() || UNTITLED,
    body: draft.body,
    content_warnings: draft.content_warnings,
    content_note: draft.content_note.trim() || null,
  }
}

const same = (a: Draft, b: Draft) => JSON.stringify(a) === JSON.stringify(b)

// La copie de secours, sur cet appareil : si la connexion coupe ou l'onglet se ferme, rien n'est perdu.
type Backup = { draft: Draft; at: number }
const backupKey = (id: number | null) => `troolplay:histoire:${id ?? 'nouvelle'}`

function readBackup(id: number | null): Backup | null {
  try {
    const raw = localStorage.getItem(backupKey(id))
    return raw ? (JSON.parse(raw) as Backup) : null
  } catch {
    return null
  }
}

function writeBackup(id: number | null, draft: Draft) {
  try {
    localStorage.setItem(backupKey(id), JSON.stringify({ draft, at: Date.now() }))
  } catch {
    // Navigation privée, ou mémoire pleine : on compte sur l'enregistrement en ligne.
  }
}

function dropBackup(id: number | null) {
  try {
    localStorage.removeItem(backupKey(id))
  } catch {
    // Rien à faire.
  }
}

function errorOf(failure: unknown): ApiError | null {
  return failure instanceof ApiError ? failure : null
}

function statusText(status: Status, published: boolean, savedAt: Date | null): string {
  if (status === 'saving') return 'Enregistrement…'
  if (status === 'error') return 'Pas enregistré. Ton texte reste gardé sur cet appareil.'
  if (status === 'unsaved') return published ? 'Corrections pas encore enregistrées' : 'Modifications en cours…'
  if (!savedAt) return published ? 'Publiée' : 'Brouillon'
  const time = savedAt.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
  return `${published ? 'Publiée' : 'Brouillon'}, enregistré à ${time}`
}

type EditorProps = {
  initial: Story | null
  characters: MyCharacter[]
  defaultCharacter: number
  /** La première sauvegarde a créé l'histoire : la page la connaît désormais. */
  onCreated: (id: number) => void
}

function Editor({ initial, characters, defaultCharacter, onCreated }: EditorProps) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const toast = useToast()

  const empty: Draft = { character_id: defaultCharacter, title: '', body: '', content_warnings: [], content_note: '' }
  const start = initial ? fromStory(initial) : empty
  const [draft, setDraft] = useState<Draft>(start)
  const [saved, setSaved] = useState<Draft>(start)
  const [storyId, setStoryId] = useState<number | null>(initial?.id ?? null)
  const [published, setPublished] = useState(initial?.published ?? false)
  const [activity, setActivity] = useState<Activity>('idle')
  const [savedAt, setSavedAt] = useState<Date | null>(null)
  const [failure, setFailure] = useState<ApiError | null>(null)
  const [preview, setPreview] = useState(false)
  // Une version plus récente gardée sur cet appareil, qu'on propose de reprendre.
  const [offer, setOffer] = useState<Backup | null>(() => {
    const backup = readBackup(initial?.id ?? null)
    if (!backup || same(backup.draft, start)) return null
    if (initial && backup.at <= Date.parse(initial.updated_at)) return null
    return backup
  })

  const body = useRef<HTMLTextAreaElement>(null)
  // La dernière version, lue par les enregistrements qui partent après un délai.
  const latest = useRef(draft)
  const idRef = useRef(storyId)
  const saving = useRef(false)
  const again = useRef(false)

  const dirty = !same(draft, saved)
  const status: Status = activity === 'idle' ? (dirty ? 'unsaved' : 'saved') : activity
  const canSave = draft.character_id > 0 && (draft.title.trim() !== '' || draft.body.trim() !== '')
  const errors = failure?.fields ?? {}

  function replace(next: Draft) {
    latest.current = next
    setDraft(next)
  }

  function set<K extends keyof Draft>(key: K, value: Draft[K]) {
    replace({ ...latest.current, [key]: value })
  }

  /** Enregistre la version du moment. Un seul envoi à la fois : une frappe pendant l'envoi en relance un. */
  async function save(): Promise<boolean> {
    if (saving.current) {
      again.current = true
      return false
    }
    const sent = latest.current
    saving.current = true
    setActivity('saving')
    try {
      const fields = toFields(sent)
      const story = idRef.current === null ? await createStory(fields) : await updateStory(idRef.current, fields)
      if (idRef.current === null) {
        idRef.current = story.id
        setStoryId(story.id)
        dropBackup(null)
        onCreated(story.id)
        // L'adresse change, l'éditeur reste : la page ne se recharge pas sous les doigts.
        navigate(`/histoires/${story.id}/modifier`, { replace: true })
      }
      queryClient.setQueryData(['story', story.id], story)
      void queryClient.invalidateQueries({ queryKey: ['stories', 'mine'] })
      setSaved(sent)
      setSavedAt(new Date())
      setFailure(null)
      setActivity('idle')
      if (same(latest.current, sent)) dropBackup(story.id)
      return true
    } catch (error) {
      setFailure(errorOf(error) ?? new ApiError(0, 'Le panneau ne répond pas.'))
      setActivity('error')
      return false
    } finally {
      saving.current = false
      if (again.current) {
        again.current = false
        void save()
      }
    }
  }

  // Chaque modification part dans la copie de secours, puis, pour un brouillon, en ligne.
  useEffect(() => {
    if (!dirty) return
    writeBackup(idRef.current, draft)
    if (published || !canSave) return
    const timer = setTimeout(() => void save(), AUTOSAVE_DELAY)
    return () => clearTimeout(timer)
    // save lit toujours la dernière version : pas besoin de la suivre.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [draft, dirty, published, canSave])

  // Quitter la page avec un texte pas encore enregistré : le navigateur demande confirmation.
  useEffect(() => {
    if (!dirty) return
    function warn(event: BeforeUnloadEvent) {
      event.preventDefault()
    }
    window.addEventListener('beforeunload', warn)
    return () => window.removeEventListener('beforeunload', warn)
  }, [dirty])

  const publish = useMutation({
    mutationFn: async () => {
      if (dirty || idRef.current === null) {
        if (!(await save())) throw new ApiError(0, "L'histoire n'a pas pu être enregistrée.")
      }
      return publishStory(idRef.current!)
    },
    onSuccess: (story) => {
      setPublished(true)
      queryClient.setQueryData(['story', story.id], story)
      void queryClient.invalidateQueries({ queryKey: ['stories'] })
      toast.show('Histoire publiée : les membres peuvent la lire.', 'success')
    },
    onError: (error) => setFailure(errorOf(error)),
  })

  const unpublish = useMutation({
    mutationFn: () => unpublishStory(idRef.current!),
    onSuccess: (story) => {
      setPublished(false)
      queryClient.setQueryData(['story', story.id], story)
      void queryClient.invalidateQueries({ queryKey: ['stories'] })
      toast.show('Histoire retirée : elle redevient un brouillon.', 'success')
    },
    onError: (error) => toast.show(`Pas retirée : ${error.message}`, 'error'),
  })

  /** Entoure la sélection de * ou de ** : les boutons, et Ctrl+I, Ctrl+B. */
  function wrap(mark: string) {
    const el = body.current
    if (!el) return
    const { selectionStart: from, selectionEnd: to, value } = el
    const selected = value.slice(from, to)
    // Déjà entouré : on retire la mise en forme.
    if (value.slice(from - mark.length, from) === mark && value.slice(to, to + mark.length) === mark) {
      set('body', value.slice(0, from - mark.length) + selected + value.slice(to + mark.length))
      requestAnimationFrame(() => el.setSelectionRange(from - mark.length, to - mark.length))
      return
    }
    set('body', value.slice(0, from) + mark + selected + mark + value.slice(to))
    requestAnimationFrame(() => {
      el.focus()
      el.setSelectionRange(from + mark.length, to + mark.length)
    })
  }

  function shortcuts(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (!(event.ctrlKey || event.metaKey) || event.altKey) return
    const key = event.key.toLowerCase()
    if (key === 'i' || key === 'b') {
      event.preventDefault()
      wrap(key === 'b' ? '**' : '*')
    }
  }

  // Un groupe par serveur, sans répétition : le menu ne titre que des options qui se suivent.
  // Les serveurs dans l'ordre où ils apparaissent dans la barre, et les personnages dans cet ordre aussi.
  const servers = [...new Set(characters.map((c) => c.server?.name ?? ''))]
  const options = servers.flatMap((server) =>
    characters
      .filter((c) => (c.server?.name ?? '') === server)
      .map((c) => ({ value: c.id, label: c.name, group: server || undefined })),
  )
  const signing = characters.find((c) => c.id === draft.character_id)
  const nearLimit = draft.body.length > BODY_MAX * 0.9
  const blocking = failure && failure.status !== 422 && failure.status !== 0

  return (
    <>
      {offer && (
        <Notice>
          <p>Une version plus récente de ce texte est restée sur cet appareil, sans avoir été enregistrée.</p>
          <div className={styles.row}>
            <Button
              onClick={() => {
                replace(offer.draft)
                setOffer(null)
              }}
            >
              La reprendre
            </Button>
            <Button
              variant="secondary"
              onClick={() => {
                dropBackup(storyId)
                setOffer(null)
              }}
            >
              Garder celle-ci
            </Button>
          </div>
        </Notice>
      )}

      {blocking && (
        <Notice tone="error">
          <p>{failure.message}</p>
        </Notice>
      )}

      <Sheet seed={`histoire-${storyId ?? 'nouvelle'}`} as="section" contentClassName={styles.card}>
        <div className={styles.row}>
          <Menu
            label="Signée par"
            value={draft.character_id}
            options={options}
            onChange={(id) => set('character_id', id)}
            placeholder="Choisir un personnage"
            error={errors.character_id}
          />
          {signing?.inactive && <span className={styles.hint}>En retrait : il peut raconter ses souvenirs, ou ce qu'il fait loin des autres.</span>}
        </div>

        <Field label="Titre" name="title" value={draft.title} onChange={(v) => set('title', v)} maxLength={TITLE_MAX} error={errors.title} />

        <div className={styles.editor}>
          <div className={styles.toolbar}>
            <div className={styles.modes} role="group" aria-label="Affichage">
              <button type="button" aria-pressed={!preview} onClick={() => setPreview(false)}>
                Écrire
              </button>
              <button type="button" aria-pressed={preview} onClick={() => setPreview(true)}>
                Aperçu
              </button>
            </div>
            {!preview && (
              <div className={styles.marks} role="group" aria-label="Mise en forme">
                <button type="button" onClick={() => wrap('*')} title="Italique (Ctrl+I)" aria-label="Italique">
                  <em>I</em>
                </button>
                <button type="button" onClick={() => wrap('**')} title="Gras (Ctrl+B)" aria-label="Gras">
                  <strong>G</strong>
                </button>
              </div>
            )}
          </div>
          {preview ? (
            <div className={styles.preview}>
              {draft.body.trim() ? <StoryText body={draft.body} /> : <p className={styles.hint}>Rien à montrer pour l'instant.</p>}
            </div>
          ) : (
            <textarea
              ref={body}
              aria-label="Ton histoire"
              className={styles.body}
              value={draft.body}
              onChange={(event) => set('body', event.target.value)}
              onKeyDown={shortcuts}
              maxLength={BODY_MAX}
              aria-invalid={errors.body ? true : undefined}
              aria-describedby="aide-texte"
              placeholder="Il était une fois, à Astrub…"
            />
          )}
          <p id="aide-texte" className={styles.hint}>
            Une ligne vide entre deux paragraphes. *Italique* et **gras** entre astérisques, comme sur Discord.{' '}
            <span className={nearLimit ? styles.limit : undefined}>
              {draft.body.length.toLocaleString('fr-FR')} / {BODY_MAX.toLocaleString('fr-FR')} caractères.
            </span>
          </p>
          {errors.body && <p className={styles.error}>{errors.body}</p>}
        </div>

        <MultiChips
          legend="Avertir le lecteur"
          options={WARNING_OPTIONS}
          value={draft.content_warnings}
          onChange={(v) => set('content_warnings', v)}
        />
        <p className={styles.hint}>
          Si ton histoire aborde l'un de ces thèmes, coche-le : le texte restera caché jusqu'à ce que le lecteur choisisse de
          le lire. Les scènes explicites restent interdites, avertissement ou non.
        </p>
        <Field
          label="Précision, si tu veux"
          name="content_note"
          value={draft.content_note}
          onChange={(v) => set('content_note', v)}
          maxLength={NOTE_MAX}
          hint="Par exemple : mort d'un personnage aimé."
          error={errors.content_note}
        />

        <div className={styles.footer}>
          <p className={styles.status} aria-live="polite">
            {statusText(status, published, savedAt)}
          </p>
          <div className={styles.row}>
            {published ? (
              <>
                <Button variant="secondary" busy={unpublish.isPending} onClick={() => unpublish.mutate()}>
                  Retirer
                </Button>
                <Button busy={status === 'saving'} disabled={!dirty || !canSave} onClick={() => void save()}>
                  Enregistrer les corrections
                </Button>
              </>
            ) : (
              <>
                {status === 'error' && (
                  <Button variant="secondary" disabled={!canSave} onClick={() => void save()}>
                    Réessayer
                  </Button>
                )}
                <Button busy={publish.isPending} disabled={!canSave || !draft.body.trim()} onClick={() => publish.mutate()}>
                  Publier
                </Button>
              </>
            )}
          </div>
        </div>
      </Sheet>

      {storyId !== null && <DeleteStory id={storyId} />}
    </>
  )
}

function DeleteStory({ id }: { id: number }) {
  const [confirming, setConfirming] = useState(false)
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const toast = useToast()
  const remove = useMutation({
    mutationFn: () => deleteStory(id),
    onSuccess: async () => {
      dropBackup(id)
      queryClient.removeQueries({ queryKey: ['story', id] })
      await queryClient.invalidateQueries({ queryKey: ['stories'] })
      toast.show('Histoire supprimée.', 'success')
      navigate('/compte')
    },
    onError: (error) => toast.show(`Pas supprimée : ${error.message}`, 'error'),
  })

  return (
    <div className={styles.delete}>
      {confirming ? (
        <>
          <span>Elle disparaîtra pour de bon.</span>
          <Button variant="secondary" onClick={() => setConfirming(false)}>
            Non, la garder
          </Button>
          <Button variant="danger" busy={remove.isPending} onClick={() => remove.mutate()}>
            Supprimer définitivement
          </Button>
        </>
      ) : (
        <button type="button" className={styles.linkButton} onClick={() => setConfirming(true)}>
          Supprimer cette histoire
        </button>
      )}
    </div>
  )
}

/** /histoires/nouvelle et /histoires/:id/modifier : écrire, sans jamais perdre son texte. */
function WriteStoryPage() {
  const { id } = useParams()
  const location = useLocation()
  const me = useMe()
  const mine = useMyCharacters()
  const active = useActiveCharacter()
  const storyId = id ? Number(id) : null
  // Une histoire qu'on vient de créer depuis cette page : l'éditeur la tient déjà, inutile de la recharger.
  // Gardé ici et non dans l'historique : après un rechargement, on relit l'histoire enregistrée.
  const [adopted, setAdopted] = useState<number | null>(null)
  const created = storyId !== null && adopted === storyId
  const story = useQuery({
    queryKey: ['story', storyId],
    queryFn: () => fetchStory(storyId!),
    enabled: storyId !== null && !created,
  })

  const heading = storyId === null || created ? 'Écrire une histoire' : story.data ? `Modifier « ${story.data.title} »` : 'Modifier une histoire'
  const page = (content: ReactNode) => (
    <main className={styles.page}>
      <PageTitle>{heading}</PageTitle>
      <h1 className={styles.title}>{heading}</h1>
      {content}
    </main>
  )

  if (me.isError) return <Unreachable />
  if (me.isPending) return null
  if (!me.data) return <Navigate to={`/connexion?suite=${encodeURIComponent(location.pathname)}`} replace />
  if (mine === undefined) return null
  if (mine.length === 0) {
    return page(
      <Notice>
        <p>
          Une histoire est signée par un de tes personnages. <Link to="/personnages/nouveau">Présente d'abord le tien.</Link>
        </p>
      </Notice>,
    )
  }
  if (storyId !== null && !created) {
    if (story.isPending) return null
    if (story.isError) {
      const missing = story.error instanceof ApiError && story.error.status === 404
      return missing ? page(<Notice tone="error"><p>Cette histoire n'existe pas, ou plus.</p></Notice>) : <Unreachable />
    }
    if (!story.data.is_mine) {
      return page(
        <Notice tone="error">
          <p>Seul son auteur peut modifier cette histoire.</p>
        </Notice>,
      )
    }
  }

  return page(
    <Editor
      // Passer de « nouvelle » à son adresse définitive ne recrée pas l'éditeur.
      key={created ? 'nouvelle' : (storyId ?? 'nouvelle')}
      initial={storyId !== null && !created ? (story.data ?? null) : null}
      characters={mine}
      defaultCharacter={active?.id ?? mine[0].id}
      onCreated={setAdopted}
    />,
  )
}

export default WriteStoryPage
