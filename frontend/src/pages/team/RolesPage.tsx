import { useMutation, useQuery } from '@tanstack/react-query'
import { type FormEvent, useState } from 'react'
import { Link, useNavigate } from 'react-router'
import { ApiError } from '../../api/client'
import { fetchTeam, lookupAccount } from '../../api/moderation'
import Button from '../../components/Button'
import Field from '../../components/Field'
import PageTitle from '../../components/PageTitle'
import Sheet from '../../components/Sheet'
import { ROLE_LABELS } from '../../lib/moderation'
import TeamGuard from './TeamGuard'
import styles from './Team.module.css'

/** /equipe/roles : qui est dans l'équipe, et retrouver un compte pour lui donner un rôle (#81). */
function Roles() {
  const navigate = useNavigate()
  const team = useQuery({ queryKey: ['moderation', 'team'], queryFn: fetchTeam })
  const [email, setEmail] = useState('')
  const lookup = useMutation({ mutationFn: lookupAccount, onSuccess: ({ id }) => navigate(`/equipe/comptes/${id}`) })
  const failure = lookup.error instanceof ApiError ? lookup.error : null

  function submit(event: FormEvent) {
    event.preventDefault()
    if (email.trim()) lookup.mutate(email.trim())
  }

  return (
    <main className={styles.page}>
      <PageTitle>Rôles</PageTitle>
      <div className={`paper-tag ${styles.head}`}>
        <h1>Rôles</h1>
        <Link to="/equipe" className={styles.crumb}>
          Espace équipe
        </Link>
      </div>

      <Sheet seed="equipe-roles-recherche" contentClassName={styles.card}>
        <h2>Donner un rôle</h2>
        <p className={styles.muted}>
          Tape l'adresse exacte de la personne : tu arrives sur son compte, où changer son rôle. Aucune liste d'adresses
          n'est jamais affichée. On peut aussi passer par l'encadré « Équipe » d'un de ses personnages.
        </p>
        <form onSubmit={submit} className={styles.actions}>
          <Field label="Son adresse email" name="email" type="email" value={email} onChange={setEmail} autoComplete="off" error={failure?.status === 404 ? failure.message : undefined} />
          <div className={styles.end}>
            <Button type="submit" busy={lookup.isPending} disabled={!email.trim()}>
              Trouver le compte
            </Button>
          </div>
        </form>
      </Sheet>

      <Sheet seed="equipe-roles-liste" contentClassName={styles.card}>
        <h2>L'équipe</h2>
        {team.data?.length ? (
          <ul className={styles.list}>
            {team.data.map((m) => (
              <li key={m.id} className={styles.row}>
                <span>
                  <strong>
                    <Link to={`/equipe/comptes/${m.id}`}>Compte n°{m.id}</Link>
                  </strong>{' '}
                  <span className={styles.muted}>{m.characters.join(', ') || 'aucun personnage'}</span>
                </span>
                <span className={styles.badges}>
                  <span className={styles.badge}>{ROLE_LABELS[m.role]}</span>
                  {m.suspended && <span className={`${styles.badge} ${styles.alert}`}>Suspendu</span>}
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <p className={styles.muted}>{team.isPending ? 'On rassemble l’équipe…' : 'Personne pour l’instant.'}</p>
        )}
      </Sheet>
    </main>
  )
}

function RolesPage() {
  return (
    <TeamGuard capability="manage_roles">
      <Roles />
    </TeamGuard>
  )
}

export default RolesPage
