import { useMutation } from '@tanstack/react-query'
import { type FormEvent, useState } from 'react'
import { Link } from 'react-router'
import { forgotPassword } from '../api/accounts'
import { ApiError } from '../api/client'
import Button from '../components/Button'
import Field from '../components/Field'
import Notice from '../components/Notice'
import Sheet from '../components/Sheet'
import PageTitle from '../components/PageTitle'
import styles from './AuthPages.module.css'

function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const forgot = useMutation({ mutationFn: forgotPassword })
  const error = forgot.error instanceof ApiError ? forgot.error : null

  function submit(event: FormEvent) {
    event.preventDefault()
    forgot.mutate(email)
  }

  return (
    <main className={styles.page}>
      <PageTitle>Mot de passe oublié</PageTitle>
      <Sheet seed="oubli" as="section">
        <form className={styles.form} onSubmit={submit} noValidate>
          <h1 className={styles.title}>Mot de passe oublié</h1>
          {forgot.isSuccess ? (
            <>
              <Notice tone="success">
                <p>{forgot.data.detail}</p>
              </Notice>
              <p className={styles.lead}>Le lien est valable une heure.</p>
            </>
          ) : (
            <>
              <p className={styles.lead}>Donne ton adresse, on t'envoie un lien pour en choisir un nouveau.</p>
              {error && error.status !== 422 && (
                <Notice tone="error">
                  <p>{error.message}</p>
                </Notice>
              )}
              <Field label="Adresse email" name="email" type="email" value={email} onChange={setEmail} autoComplete="email" required error={error?.fields.email} />
              <Button type="submit" busy={forgot.isPending}>
                Envoyer le lien
              </Button>
            </>
          )}
          <div className={styles.links}>
            <Link to="/connexion">Retour à la connexion</Link>
          </div>
        </form>
      </Sheet>
    </main>
  )
}

export default ForgotPasswordPage
