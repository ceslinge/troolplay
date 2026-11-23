import { useMutation } from '@tanstack/react-query'
import { type FormEvent, useState } from 'react'
import { Link, useSearchParams } from 'react-router'
import { resetPassword } from '../api/accounts'
import { ApiError } from '../api/client'
import Button from '../components/Button'
import Field from '../components/Field'
import Notice from '../components/Notice'
import Sheet from '../components/Sheet'
import styles from './AuthPages.module.css'

function ResetPasswordPage() {
  const [params] = useSearchParams()
  const token = params.get('jeton') ?? ''
  const [password, setPassword] = useState('')
  const reset = useMutation({ mutationFn: resetPassword })
  const error = reset.error instanceof ApiError ? reset.error : null

  function submit(event: FormEvent) {
    event.preventDefault()
    reset.mutate({ token, password })
  }

  return (
    <main className={styles.page}>
      <Sheet seed="nouveau-mot-de-passe" as="section">
        <form className={styles.form} onSubmit={submit} noValidate>
          <h1 className={styles.title}>Choisir un nouveau mot de passe</h1>
          {reset.isSuccess ? (
            <>
              <Notice tone="success">
                <p>C'est fait. Par sécurité, toutes tes sessions ont été fermées : reconnecte-toi avec ton nouveau mot de passe.</p>
              </Notice>
              <Link to="/connexion">Se connecter</Link>
            </>
          ) : (
            <>
              {error && error.status !== 422 && (
                <Notice tone="error">
                  <p>{error.status === 400 ? "Ce lien n'est plus valable : il a déjà servi, ou il a expiré." : error.message}</p>
                  {error.status === 400 && (
                    <p>
                      <Link to="/mot-de-passe-oublie">Demander un nouveau lien</Link>
                    </p>
                  )}
                </Notice>
              )}
              <Field
                label="Nouveau mot de passe"
                name="password"
                type="password"
                value={password}
                onChange={setPassword}
                autoComplete="new-password"
                required
                hint="10 caractères au moins."
                error={error?.fields.password}
              />
              <Button type="submit" busy={reset.isPending}>
                Enregistrer
              </Button>
            </>
          )}
        </form>
      </Sheet>
    </main>
  )
}

export default ResetPasswordPage
