import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link, useParams } from 'react-router'
import { changeRole, type Duration, fetchJournal, fetchTeamAccount, reinstate, type Role, setReporting, suspend } from '../../api/moderation'
import Button from '../../components/Button'
import PageTitle from '../../components/PageTitle'
import ReasonForm from '../../components/ReasonForm'
import Sheet from '../../components/Sheet'
import { ACTION_LABELS, actorLabel, detailLabel, DURATION_LABELS, ROLE_LABELS, teamDate } from '../../lib/moderation'
import { useToast } from '../../lib/toast'
import { useCan } from '../../lib/useCan'
import TeamGuard from './TeamGuard'
import styles from './Team.module.css'

type Acting = 'suspend' | 'reinstate' | 'reporting' | 'role' | null

function Account({ id }: { id: number }) {
  const queryClient = useQueryClient()
  const toast = useToast()
  const canBan = useCan('ban')
  const canManageRoles = useCan('manage_roles')
  const [role, setRole] = useState<Role | null>(null)
  const account = useQuery({ queryKey: ['moderation', 'account', id], queryFn: () => fetchTeamAccount(id) })
  const history = useQuery({ queryKey: ['moderation', 'journal', { targetUserId: id }], queryFn: () => fetchJournal({ targetUserId: id }) })
  const [acting, setActing] = useState<Acting>(null)
  const [duration, setDuration] = useState<Duration | null>(null)

  const act = useMutation({
    mutationFn: (reason: string) => {
      const a = account.data!
      if (acting === 'suspend') return suspend(id, duration!, reason)
      if (acting === 'reinstate') return reinstate(id, reason)
      if (acting === 'role') return changeRole(id, role!, reason)
      return setReporting(id, a.reporting_revoked, reason)
    },
    onSuccess: async () => {
      toast.show('C’est fait, et c’est au journal.', 'success')
      setActing(null)
      setDuration(null)
      setRole(null)
      await queryClient.invalidateQueries({ queryKey: ['moderation'] })
    },
  })

  if (account.isPending) return null
  if (account.isError) return <p className={styles.muted}>Ce compte est introuvable.</p>
  const a = account.data

  return (
    <>
      <PageTitle>{`Compte n°${a.id}`}</PageTitle>
      <div className={styles.head}>
        <h1>Compte n°{a.id}</h1>
        <Link to="/equipe" className={styles.crumb}>
          Espace équipe
        </Link>
      </div>
      <Sheet seed={`equipe-compte-${a.id}`} contentClassName={styles.card}>
        <dl className={styles.facts}>
          <dt>Rôle</dt>
          <dd>{ROLE_LABELS[a.role]}</dd>
          <dt>Depuis le</dt>
          <dd>
            {new Date(a.created_at).toLocaleDateString('fr-FR', { dateStyle: 'long' })}
            {!a.verified && ', adresse pas encore vérifiée'}
          </dd>
          <dt>État</dt>
          <dd>
            {a.suspended
              ? a.banned_until
                ? `Suspendu jusqu'au ${teamDate(a.banned_until)}`
                : 'Banni, sans date de fin'
              : 'Actif'}
            {a.reporting_revoked && ' · ne peut plus signaler'}
          </dd>
          <dt>Personnages</dt>
          <dd>
            {a.characters.length === 0
              ? 'Aucun'
              : a.characters.map((c, i) => (
                  <span key={c.id}>
                    {i > 0 && ', '}
                    <Link to={`/personnages/${c.id}`}>{c.name}</Link>
                    {c.server && ` (${c.server})`}
                    {c.hidden && ', masqué'}
                  </span>
                ))}
          </dd>
          <dt>Signalements</dt>
          <dd>
            {a.reports_received} reçu{a.reports_received > 1 ? 's' : ''}, {a.reports_sent} envoyé{a.reports_sent > 1 ? 's' : ''}
          </dd>
        </dl>
        <p className={styles.muted}>
          L'adresse email n'apparaît jamais ici. Ce que tu vois de ce compte reste dans l'équipe (charte de modération).
        </p>

        {acting === null ? (
          <div className={styles.actions}>
            {canBan &&
              (a.suspended ? (
                <Button variant="secondary" onClick={() => setActing('reinstate')}>
                  Lever la suspension
                </Button>
              ) : (
                <Button variant="danger" onClick={() => setActing('suspend')}>
                  Suspendre
                </Button>
              ))}
            <Button variant="secondary" onClick={() => setActing('reporting')}>
              {a.reporting_revoked ? 'Rendre le droit de signaler' : 'Retirer le droit de signaler'}
            </Button>
            {canManageRoles && (
              <Button variant="secondary" onClick={() => setActing('role')}>
                Changer le rôle
              </Button>
            )}
          </div>
        ) : (
          <ReasonForm
            title={
              acting === 'suspend'
                ? 'Suspendre ce compte'
                : acting === 'role'
                  ? 'Changer le rôle'
                  : acting === 'reinstate'
                  ? 'Lever la suspension'
                  : a.reporting_revoked
                    ? 'Rendre le droit de signaler'
                    : 'Retirer le droit de signaler'
            }
            confirm={acting === 'suspend' ? 'Suspendre' : 'Confirmer'}
            danger={acting === 'suspend'}
            busy={act.isPending}
            error={act.error}
            hint={acting === 'role' ? 'Envoyée à la personne avec son nouveau rôle, et gardée au journal.' : undefined}
            ready={(acting !== 'suspend' || duration !== null) && (acting !== 'role' || role !== null)}
            onConfirm={(reason) => act.mutate(reason)}
            onCancel={() => setActing(null)}
          >
            {acting === 'role' && (
              <fieldset className={styles.choices}>
                {(Object.keys(ROLE_LABELS) as Role[])
                  .filter((r) => r !== a.role)
                  .map((r) => (
                    <label key={r}>
                      <input type="radio" name="role" checked={role === r} onChange={() => setRole(r)} />
                      <span>{ROLE_LABELS[r]}</span>
                    </label>
                  ))}
              </fieldset>
            )}
            {acting === 'suspend' && (
              <fieldset className={styles.choices}>
                {(Object.keys(DURATION_LABELS) as Duration[]).map((d) => (
                  <label key={d}>
                    <input type="radio" name="duree" checked={duration === d} onChange={() => setDuration(d)} />
                    <span>{DURATION_LABELS[d]}</span>
                  </label>
                ))}
              </fieldset>
            )}
          </ReasonForm>
        )}
      </Sheet>

      <Sheet seed={`equipe-compte-${a.id}-journal`} contentClassName={styles.card}>
        <h2>Ce que l'équipe a décidé pour ce compte</h2>
        {history.data?.items.length ? (
          <ul className={styles.list}>
            {history.data.items.map((e) => (
              <li key={e.id} className={styles.row}>
                <span>
                  <strong>{ACTION_LABELS[e.action] ?? e.action}</strong>
                  {e.detail && ` (${detailLabel(e.detail)})`} : {e.reason}
                </span>
                <span className={styles.muted}>
                  le {teamDate(e.created_at)}, {actorLabel(e.actor_id, e.action)}
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <p className={styles.muted}>Rien pour l'instant.</p>
        )}
      </Sheet>
    </>
  )
}

function TeamAccountPage() {
  const { id = '' } = useParams()
  return (
    <TeamGuard>
      <main className={styles.page}>
        <Account id={Number(id)} />
      </main>
    </TeamGuard>
  )
}

export default TeamAccountPage
