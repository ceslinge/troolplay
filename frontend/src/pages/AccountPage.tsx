import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { type FormEvent, useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router'
import { changePassword, deleteAccount, logOut } from '../api/accounts'
import { fetchMyCharacters, MAX_CHARACTERS } from '../api/characters'
import CharacterCard from '../components/CharacterCard'
import CharacterOrder from '../components/CharacterOrder'
import MyStories from '../components/MyStories'
import { ApiError } from '../api/client'
import Button from '../components/Button'
import Field from '../components/Field'
import Notice from '../components/Notice'
import Sheet from '../components/Sheet'
import { useMe } from '../lib/useMe'
import PageTitle from '../components/PageTitle'
import Unreachable from '../components/Unreachable'
import { useToast } from '../lib/toast'
import styles from './AuthPages.module.css'

function MyCharacters() {
  const mine = useQuery({ queryKey: ['characters', 'mine'], queryFn: fetchMyCharacters })
  const [ordering, setOrdering] = useState(false)
  const count = mine.data?.length ?? 0

  return (
    <section className={styles.mine}>
      <div className={styles.mineHead}>
        <h2 className={styles.title}>Mes personnages</h2>
        <div className={styles.mineActions}>
          {count > 1 && (
            <button type="button" className={styles.linkButton} aria-pressed={ordering} onClick={() => setOrdering(!ordering)}>
              {ordering ? 'Terminer' : 'Changer l’ordre'}
            </button>
          )}
          {count >= MAX_CHARACTERS ? (
            <span className={styles.lead}>Pas de nouveau personnage possible ({MAX_CHARACTERS} au plus).</span>
          ) : (
            <Link to="/personnages/nouveau">Présenter un nouveau personnage</Link>
          )}
        </div>
      </div>
      {mine.isPending ? null : mine.isError ? (
        <Notice tone="error">
          <p>Impossible de charger tes personnages pour l'instant.</p>
        </Notice>
      ) : mine.data.length === 0 ? (
        <Notice>
          <p>Pas encore de personnage sur le panneau. Le premier t'attend.</p>
        </Notice>
      ) : ordering && count > 1 ? (
        <CharacterOrder characters={mine.data} />
      ) : (
        <div className={styles.grid}>
          {mine.data.map((character) => (
            <CharacterCard key={character.id} character={character} />
          ))}
        </div>
      )}
    </section>
  )
}

function ChangePasswordForm() {
  const [current, setCurrent] = useState('')
  const [next, setNext] = useState('')
  const change = useMutation({
    mutationFn: changePassword,
    onSuccess: () => {
      setCurrent('')
      setNext('')
    },
  })
  const error = change.error instanceof ApiError ? change.error : null

  function submit(event: FormEvent) {
    event.preventDefault()
    change.mutate({ current_password: current, new_password: next })
  }

  return (
    <form className={styles.form} onSubmit={submit} noValidate>
      <h2 className={styles.title}>Changer de mot de passe</h2>
      {change.isSuccess && (
        <Notice tone="success">
          <p>Mot de passe changé. Tes autres appareils ont été déconnectés.</p>
        </Notice>
      )}
      {error && error.status !== 422 && (
        <Notice tone="error">
          <p>{error.message}</p>
        </Notice>
      )}
      <Field label="Mot de passe actuel" name="current_password" type="password" value={current} onChange={setCurrent} autoComplete="current-password" required />
      <Field
        label="Nouveau mot de passe"
        name="new_password"
        type="password"
        value={next}
        onChange={setNext}
        autoComplete="new-password"
        required
        hint="10 caractères au moins."
        error={error?.fields.new_password}
      />
      <Button type="submit" busy={change.isPending}>
        Changer
      </Button>
    </form>
  )
}

function DeleteAccountForm({ onDeleted }: { onDeleted: () => void }) {
  const [password, setPassword] = useState('')
  const remove = useMutation({ mutationFn: deleteAccount, onSuccess: onDeleted })
  const error = remove.error instanceof ApiError ? remove.error : null

  function submit(event: FormEvent) {
    event.preventDefault()
    remove.mutate(password)
  }

  return (
    <form className={styles.form} onSubmit={submit} noValidate>
      <h2 className={styles.title}>Supprimer mon compte</h2>
      <p className={styles.lead}>
        Ton compte, tous tes personnages et tes histoires disparaîtront pour de bon. On ne pourra pas les récupérer.
      </p>
      {error && (
        <Notice tone="error">
          <p>{error.message}</p>
        </Notice>
      )}
      <Field label="Ton mot de passe, pour confirmer" name="password" type="password" value={password} onChange={setPassword} autoComplete="current-password" required />
      <Button type="submit" variant="danger" busy={remove.isPending}>
        Supprimer définitivement
      </Button>
    </form>
  )
}

function AccountPage() {
  const me = useMe()
  const queryClient = useQueryClient()
  const navigate = useNavigate()

  async function leave() {
    queryClient.setQueryData(['me'], null)
    // Ce qui a été chargé connecté ne doit pas resservir au visiteur qui suit.
    await queryClient.invalidateQueries({ predicate: (query) => query.queryKey[0] !== 'me' })
    navigate('/')
  }
  const toast = useToast()
  const logout = useMutation({
    mutationFn: logOut,
    onSuccess: leave,
    onError: (failure) => toast.show(`Pas déconnecté : ${failure.message}`, 'error'),
  })

  if (me.isPending) {
    return null
  }
  if (me.isError) {
    return <Unreachable />
  }
  if (!me.data) {
    return <Navigate to="/connexion?suite=/compte" replace />
  }

  return (
    <main className={`${styles.page} ${styles.wide}`}>
      <PageTitle>Mon compte</PageTitle>
      <Sheet seed="compte" as="section">
        <div className={styles.form}>
          <h1 className={styles.title}>Mon compte</h1>
          <dl className={styles.facts}>
            <dt>Adresse</dt>
            <dd>{me.data.email}</dd>
            <dt>Membre depuis</dt>
            <dd>{new Date(me.data.created_at).toLocaleDateString('fr-FR', { dateStyle: 'long' })}</dd>
          </dl>
          <div>
            <Button variant="secondary" busy={logout.isPending} onClick={() => logout.mutate()}>
              Se déconnecter
            </Button>
          </div>
        </div>
      </Sheet>
      <MyCharacters />
      <MyStories />
      <Sheet seed="compte-mot-de-passe" as="section">
        <ChangePasswordForm />
      </Sheet>
      <Sheet seed="compte-suppression" as="section" variant="muted">
        <DeleteAccountForm onDeleted={leave} />
      </Sheet>
    </main>
  )
}

export default AccountPage
