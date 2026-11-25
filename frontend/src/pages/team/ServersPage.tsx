import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { type FormEvent, useState } from 'react'
import { Link } from 'react-router'
import { ApiError } from '../../api/client'
import { addServer, fetchTeamServers, renameServer, setServerOpen, type TeamServer } from '../../api/moderation'
import type { Server } from '../../api/servers'
import Button from '../../components/Button'
import Field from '../../components/Field'
import Menu from '../../components/Menu'
import Notice from '../../components/Notice'
import PageTitle from '../../components/PageTitle'
import ReasonForm from '../../components/ReasonForm'
import Sheet from '../../components/Sheet'
import { GAME_LABELS } from '../../lib/games'
import TeamGuard from './TeamGuard'
import styles from './Team.module.css'

const JOURNAL_ONLY = 'Gardée au journal de l’équipe.'
const GAMES = Object.entries(GAME_LABELS).map(([value, label]) => ({ value: value as Server['game'], label }))

type Acting = { server: TeamServer; what: 'rename' | 'close' | 'reopen' }

/** « aucune fiche », « 1 histoire », « 12 fiches » : les deux mots sont féminins. */
function count(n: number, word: string) {
  return n === 0 ? `aucune ${word}` : `${n} ${word}${n > 1 ? 's' : ''}`
}

/** Le geste en cours sur un serveur : renommer, fermer ou rouvrir, toujours avec une raison. */
function ServerAction({ acting, onDone }: { acting: Acting; onDone: () => void }) {
  const queryClient = useQueryClient()
  const { server, what } = acting
  const [name, setName] = useState(server.name)
  const act = useMutation({
    mutationFn: (reason: string) =>
      what === 'rename' ? renameServer(server.id, name.trim(), reason) : setServerOpen(server.id, what === 'reopen', reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['moderation', 'servers'] })
      queryClient.invalidateQueries({ queryKey: ['servers'] })
      onDone()
    },
  })
  const title = { rename: `Renommer ${server.name}`, close: `Fermer ${server.name}`, reopen: `Rouvrir ${server.name}` }[what]

  return (
    <ReasonForm
      title={title}
      confirm={{ rename: 'Renommer', close: 'Fermer', reopen: 'Rouvrir' }[what]}
      danger={what === 'close'}
      busy={act.isPending}
      error={act.error}
      hint={JOURNAL_ONLY}
      ready={what !== 'rename' || (name.trim().length >= 2 && name.trim() !== server.name)}
      onConfirm={(reason) => act.mutate(reason)}
      onCancel={onDone}
    >
      {what === 'rename' && <Field label="Nouveau nom" name="name" value={name} onChange={setName} maxLength={40} autoComplete="off" />}
      {what === 'close' && (
        <p className={styles.muted}>
          On ne pourra plus y présenter de personnage.{' '}
          {server.characters === 0
            ? 'Aucune fiche n’y vit pour l’instant.'
            : `Ce qui y vit reste lisible, avec la mention « serveur fermé » : ${count(server.characters, 'fiche')}, ${count(server.stories, 'histoire')}.`}
        </p>
      )}
    </ReasonForm>
  )
}

function AddServer() {
  const queryClient = useQueryClient()
  const [game, setGame] = useState<Server['game']>('dofus')
  const [name, setName] = useState('')
  const [reason, setReason] = useState('')
  const add = useMutation({
    mutationFn: () => addServer(game, name.trim(), reason.trim()),
    onSuccess: () => {
      setName('')
      setReason('')
      queryClient.invalidateQueries({ queryKey: ['moderation', 'servers'] })
      queryClient.invalidateQueries({ queryKey: ['servers'] })
    },
  })
  const failure = add.error instanceof ApiError ? add.error : null

  function submit(event: FormEvent) {
    event.preventDefault()
    if (name.trim().length >= 2 && reason.trim().length >= 3) add.mutate()
  }

  return (
    <Sheet seed="equipe-serveurs-ajout" contentClassName={styles.card}>
      <h2>Ajouter un serveur</h2>
      <p className={styles.muted}>Quand Ankama ouvre un serveur. Il apparaît tout de suite dans les choix du site.</p>
      {add.isSuccess && (
        <Notice tone="success">
          <p>{add.data.name} est ouvert.</p>
        </Notice>
      )}
      {failure && failure.status !== 422 && (
        <Notice tone="error">
          <p>{failure.message}</p>
        </Notice>
      )}
      <form onSubmit={submit} className={styles.actions}>
        <Menu label="Le jeu" value={game} options={GAMES} onChange={setGame} />
        <Field label="Son nom" name="name" value={name} onChange={setName} maxLength={40} autoComplete="off" error={failure?.fields.name} />
        <Field label="La raison" name="reason" value={reason} onChange={setReason} rows={2} maxLength={1000} hint={JOURNAL_ONLY} error={failure?.fields.reason} />
        <div className={styles.end}>
          <Button type="submit" busy={add.isPending} disabled={name.trim().length < 2 || reason.trim().length < 3}>
            Ajouter
          </Button>
        </div>
      </form>
    </Sheet>
  )
}

function Servers() {
  const servers = useQuery({ queryKey: ['moderation', 'servers'], queryFn: fetchTeamServers })
  const [acting, setActing] = useState<Acting | null>(null)
  const games = (Object.keys(GAME_LABELS) as Server['game'][]).map((game) => ({
    game,
    servers: (servers.data ?? []).filter((s) => s.game === game),
  }))

  return (
    <main className={styles.page}>
      <PageTitle>Serveurs</PageTitle>
      <div className={styles.head}>
        <h1>Serveurs</h1>
        <Link to="/equipe" className={styles.crumb}>
          Espace équipe
        </Link>
      </div>
      <AddServer />
      {servers.isError && (
        <Notice tone="error">
          <p>Impossible de charger les serveurs pour l'instant.</p>
        </Notice>
      )}
      {games.map(
        ({ game, servers: list }) =>
          list.length > 0 && (
            <Sheet key={game} seed={`equipe-serveurs-${game}`} contentClassName={styles.card}>
              <h2>{GAME_LABELS[game]}</h2>
              <ul className={styles.list}>
                {list.map((s) => (
                  <li key={s.id} className={styles.row}>
                    {acting?.server.id === s.id ? (
                      <ServerAction acting={acting} onDone={() => setActing(null)} />
                    ) : (
                      <>
                        <span>
                          <strong>{s.name}</strong>{' '}
                          <span className={styles.muted}>
                            {count(s.characters, 'fiche')} · {count(s.stories, 'histoire')}
                          </span>
                        </span>
                        <span className={styles.rowActions}>
                          {s.closed && <span className={styles.badge}>Fermé</span>}
                          <button type="button" className={styles.linkButton} onClick={() => setActing({ server: s, what: 'rename' })}>
                            Renommer
                          </button>
                          <button
                            type="button"
                            className={styles.linkButton}
                            onClick={() => setActing({ server: s, what: s.closed ? 'reopen' : 'close' })}
                          >
                            {s.closed ? 'Rouvrir' : 'Fermer'}
                          </button>
                        </span>
                      </>
                    )}
                  </li>
                ))}
              </ul>
            </Sheet>
          ),
      )}
    </main>
  )
}

function ServersPage() {
  return (
    <TeamGuard capability="manage_servers">
      <Servers />
    </TeamGuard>
  )
}

export default ServersPage
