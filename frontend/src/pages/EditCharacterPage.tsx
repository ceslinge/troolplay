import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { type FormEvent, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router'
import { type Character, deleteCharacter, fetchCharacter, replaceHangouts, updateCharacter } from '../api/characters'
import { ApiError } from '../api/client'
import { fetchServers } from '../api/servers'
import Button from '../components/Button'
import Field from '../components/Field'
import HangoutsEditor, { type HangoutDraft } from '../components/HangoutsEditor'
import Notice from '../components/Notice'
import Sheet from '../components/Sheet'
import { focusFirstError, useToast } from '../lib/toast'
import { STORY_FIELDS } from './characterFields'
import { type Draft, formParts, fromCharacter, toUpdateRequest, withChange } from './characterForm'
import styles from './CreateCharacterPage.module.css'

function toHangoutDrafts(character: Character): HangoutDraft[] {
  return character.hangouts.map((h) => ({
    area: h.area,
    x: String(h.x),
    y: String(h.y),
    label: h.label ?? '',
    habits: h.habits ?? '',
  }))
}

function EditForm({ character }: { character: Character }) {
  const servers = useQuery({ queryKey: ['servers'], queryFn: fetchServers })
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const [draft, setDraft] = useState<Draft>(() => fromCharacter(character))
  const [hangouts, setHangouts] = useState<HangoutDraft[]>(() => toHangoutDrafts(character))
  const toast = useToast()

  const save = useMutation({
    // D'abord la fiche, puis ses lieux. Si l'un échoue, le formulaire garde tout : rien n'est perdu.
    mutationFn: async () => {
      // Un lieu sans zone ou sans coordonnées ne partirait pas comme on le croit : on prévient avant d'envoyer.
      const coordinate = /^-?\d+$/
      if (hangouts.some((h) => !h.area.trim() || !coordinate.test(h.x) || !coordinate.test(h.y))) {
        throw new ApiError(422, 'Un lieu est incomplet.', {
          hangouts: 'Chaque lieu a besoin de sa zone et de ses deux coordonnées.',
        })
      }
      const changes = toUpdateRequest(draft)
      // Le serveur ne part que s'il a changé : un serveur actuel fermé ne bloque pas la fiche.
      if (draft.server_id !== String(character.server?.id ?? '')) changes.server_id = Number(draft.server_id)
      await updateCharacter(character.id, changes)
      await replaceHangouts(
        character.id,
        hangouts.map((h) => ({
          area: h.area.trim(),
          x: Number(h.x),
          y: Number(h.y),
          label: h.label.trim() || null,
          habits: h.habits.trim() || null,
        })),
      )
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['character', String(character.id)] })
      await queryClient.invalidateQueries({ queryKey: ['characters'] })
      toast.show('Fiche enregistrée.', 'success')
      navigate(`/personnages/${character.id}`)
    },
    onError: (failure) => {
      // L'erreur s'affiche sous son champ, souvent loin du bouton : on prévient, puis on y amène.
      const onField = failure instanceof ApiError && Object.keys(failure.fields).length > 0
      toast.show(onField ? 'Pas enregistré : un champ est à corriger.' : `Pas enregistré : ${failure.message}`, 'error')
      if (onField) focusFirstError()
    },
  })
  const error = save.error instanceof ApiError ? save.error : null
  const errors = error?.fields ?? {}
  // Les erreurs des lieux arrivent sans champ du formulaire principal (409, ou un lieu invalide).
  const hangoutError =
    error && (error.status === 409 || 'hangouts' in errors || Object.keys(errors).some((f) => ['area', 'x', 'y', 'label', 'habits'].includes(f)))
      ? error.status === 409
        ? error.message
        : errors.hangouts ?? 'Un lieu est incomplet : il faut au moins sa zone et ses coordonnées.'
      : undefined

  function set<K extends keyof Draft>(key: K, value: Draft[K]) {
    setDraft((current) => withChange(current, key, value, servers.data ?? []))
  }

  function submit(event: FormEvent) {
    event.preventDefault()
    save.mutate()
  }

  const server = servers.data?.find((s) => String(s.id) === draft.server_id)
  // On peut déménager, mais seulement vers un serveur ouvert du même jeu (décision 29).
  const sameGame = (servers.data ?? []).filter((s) => s.game === character.server?.game)
  const parts = formParts({ draft, set, errors, servers: sameGame, server, mode: 'free' })
  const groups: { title: string; fields: (keyof Draft)[] }[] = [
    { title: 'Qui est-ce ?', fields: ['name', 'server_id', 'gender'] },
    { title: 'En jeu', fields: ['class', 'level', 'ingame_name', 'play_days', 'play_periods'] },
    { title: 'Son histoire', fields: [...STORY_FIELDS] },
    { title: 'Hors RP', fields: ['ooc_note'] },
  ]

  return (
    <form onSubmit={submit} noValidate className={styles.stack}>
      {error && error.status !== 409 && !hangoutError && (
        <Notice tone="error">
          <p>{error.message}</p>
        </Notice>
      )}
      {groups.map((group, index) => (
        <Sheet key={group.title} seed={`edition-${group.title}`} as="section" contentClassName={styles.card}>
          <h2 className={styles.question}>{group.title}</h2>
          {index === 0 && (
            <p className={styles.hint}>
              Un transfert, une fusion, un serveur temporaire qui ferme ? Change de serveur ici : la fiche garde tout.
              On reste dans le même jeu.
            </p>
          )}
          <div className={styles.stack}>
            {group.fields.map((key) => (
              <div key={key}>{parts[key]}</div>
            ))}
          </div>
        </Sheet>
      ))}
      <Sheet seed="edition-lieux" as="section" contentClassName={styles.card}>
        <h2 className={styles.question}>Où le croiser</h2>
        <HangoutsEditor value={hangouts} onChange={setHangouts} error={hangoutError} />
      </Sheet>
      <div className={styles.nav}>
        <Link to={`/personnages/${character.id}`}>Annuler</Link>
        <Button type="submit" busy={save.isPending}>
          Enregistrer
        </Button>
      </div>
    </form>
  )
}

/** Retirer un personnage du panneau, en deux temps pour éviter l'erreur. */
function DeleteCharacter({ character }: { character: Character }) {
  const [confirming, setConfirming] = useState(false)
  const [typed, setTyped] = useState('')
  const toast = useToast()
  // Taper le nom : on ne le fait pas par réflexe, et c'est moins pénible qu'un mot de passe.
  const confirmed = typed.trim() === character.name
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const remove = useMutation({
    mutationFn: () => deleteCharacter(character.id),
    onSuccess: async () => {
      queryClient.removeQueries({ queryKey: ['character', String(character.id)] })
      await queryClient.invalidateQueries({ queryKey: ['characters'] })
      toast.show(`${character.name} a quitté le panneau.`, 'success')
      navigate('/compte')
    },
    onError: (failure) => toast.show(`Pas supprimé : ${failure.message}`, 'error'),
  })

  return (
    <Sheet seed="edition-suppression" variant="muted" as="section" contentClassName={styles.card}>
      <h2 className={styles.question}>Retirer {character.name} du panneau</h2>
      <p className={styles.hint}>La fiche et ses lieux disparaîtront pour de bon. Pour une simple pause, mieux vaut la mettre en retrait.</p>
      {remove.isError && (
        <Notice tone="error">
          <p>{remove.error.message}</p>
        </Notice>
      )}
      {confirming ? (
        <>
          <Field
            label={`Pour confirmer, tape son nom : ${character.name}`}
            name="confirm-name"
            value={typed}
            onChange={setTyped}
            autoComplete="off"
          />
          <div className={styles.nav}>
            <Button
              variant="secondary"
              onClick={() => {
                setConfirming(false)
                setTyped('')
              }}
            >
              Non, la garder
            </Button>
            <Button variant="danger" disabled={!confirmed} busy={remove.isPending} onClick={() => remove.mutate()}>
              Supprimer définitivement
            </Button>
          </div>
        </>
      ) : (
        <div>
          <Button variant="danger" onClick={() => setConfirming(true)}>
            Supprimer ce personnage
          </Button>
        </div>
      )}
    </Sheet>
  )
}

function EditCharacterPage() {
  const { id = '' } = useParams()
  const query = useQuery({ queryKey: ['character', id, 'edition'], queryFn: () => fetchCharacter(id) })

  return (
    <main className={styles.page}>
      {/* Le nom enregistré, pas celui en cours de saisie : on sait toujours quelle fiche on modifie. */}
      <h1 className={styles.title}>{query.data ? `Modifier la fiche de ${query.data.name}` : 'Modifier la fiche'}</h1>
      {query.isPending ? null : query.isError ? (
        <Notice tone="error">
          <p>Le panneau est inaccessible pour l'instant. Réessaie dans un moment.</p>
        </Notice>
      ) : !query.data ? (
        <Notice tone="error">
          <p>Cette fiche n'existe pas, ou plus.</p>
        </Notice>
      ) : !query.data.is_mine ? (
        <Notice tone="error">
          <p>Seul son propriétaire peut modifier cette fiche.</p>
        </Notice>
      ) : (
        <>
          <EditForm character={query.data} />
          <DeleteCharacter character={query.data} />
        </>
      )}
    </main>
  )
}

export default EditCharacterPage
