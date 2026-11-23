import { useMutation, useQueryClient } from '@tanstack/react-query'
import { type FormEvent, useState } from 'react'
import { Navigate, useNavigate } from 'react-router'
import { changePassword, deleteAccount, logOut } from '../api/accounts'
import { ApiError } from '../api/client'
import Button from '../components/Button'
import Field from '../components/Field'
import Notice from '../components/Notice'
import Sheet from '../components/Sheet'
import { useMe } from '../lib/useMe'
import styles from './AuthPages.module.css'

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
    navigate('/')
  }
  const logout = useMutation({ mutationFn: logOut, onSuccess: leave })

  if (me.isPending) {
    return null
  }
  if (!me.data) {
    return <Navigate to="/connexion?suite=/compte" replace />
  }

  return (
    <main className={`${styles.page} ${styles.wide}`}>
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
