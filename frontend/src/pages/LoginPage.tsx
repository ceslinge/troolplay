import { useMutation, useQueryClient } from '@tanstack/react-query'
import { type FormEvent, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router'
import { logIn } from '../api/accounts'
import { ApiError } from '../api/client'
import Button from '../components/Button'
import Field from '../components/Field'
import Notice from '../components/Notice'
import Sheet from '../components/Sheet'
import styles from './AuthPages.module.css'

function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const login = useMutation({
    mutationFn: logIn,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['me'] })
      navigate(params.get('suite') ?? '/')
    },
  })
  const error = login.error instanceof ApiError ? login.error : null

  function submit(event: FormEvent) {
    event.preventDefault()
    login.mutate({ email, password })
  }

  return (
    <main className={styles.page}>
      <Sheet seed="connexion" as="section">
        <form className={styles.form} onSubmit={submit} noValidate>
          <h1 className={styles.title}>Se connecter</h1>
          {error && (
            <Notice tone="error">
              <p>{error.message}</p>
              {error.status === 403 && error.message.includes('Vérifie') && (
                <p>
                  <Link to="/verifier">Recevoir un nouveau lien de vérification</Link>
                </p>
              )}
            </Notice>
          )}
          <Field label="Adresse email" name="email" type="email" value={email} onChange={setEmail} autoComplete="email" required error={error?.fields.email} />
          <Field label="Mot de passe" name="password" type="password" value={password} onChange={setPassword} autoComplete="current-password" required />
          <Button type="submit" busy={login.isPending}>
            Se connecter
          </Button>
          <div className={styles.links}>
            <Link to="/mot-de-passe-oublie">Mot de passe oublié ?</Link>
            <Link to="/inscription">Pas encore de compte ? S'inscrire</Link>
          </div>
        </form>
      </Sheet>
    </main>
  )
}

export default LoginPage
