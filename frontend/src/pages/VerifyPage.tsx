import { useMutation } from '@tanstack/react-query'
import { type FormEvent, useState } from 'react'
import { Link, useSearchParams } from 'react-router'
import { resendVerification, verifyEmail } from '../api/accounts'
import { ApiError } from '../api/client'
import Button from '../components/Button'
import Field from '../components/Field'
import Notice from '../components/Notice'
import Sheet from '../components/Sheet'
import styles from './AuthPages.module.css'

/** Demande un nouveau lien de vérification. */
function ResendForm() {
  const [email, setEmail] = useState('')
  const resend = useMutation({ mutationFn: resendVerification })
  const error = resend.error instanceof ApiError ? resend.error : null

  function submit(event: FormEvent) {
    event.preventDefault()
    resend.mutate(email)
  }

  if (resend.isSuccess) {
    return (
      <Notice tone="success">
        <p>{resend.data.detail}</p>
      </Notice>
    )
  }
  return (
    <form className={styles.form} onSubmit={submit} noValidate>
      <h2 className={styles.title}>Recevoir un nouveau lien</h2>
      {error && error.status !== 422 && (
        <Notice tone="error">
          <p>{error.message}</p>
        </Notice>
      )}
      <Field label="Adresse email" name="email" type="email" value={email} onChange={setEmail} autoComplete="email" required error={error?.fields.email} />
      <Button type="submit" busy={resend.isPending}>
        Envoyer le lien
      </Button>
    </form>
  )
}

/**
 * La vérification se fait d'un clic, pas à l'ouverture de la page :
 * certaines messageries ouvrent les liens toutes seules pour les inspecter,
 * et consommeraient le lien à la place de la personne.
 */
function VerifyPage() {
  const [params] = useSearchParams()
  const token = params.get('jeton')
  const verify = useMutation({ mutationFn: verifyEmail })

  return (
    <main className={styles.page}>
      <Sheet seed="verification" as="section">
        {token && !verify.isError ? (
          <div className={styles.form}>
            <h1 className={styles.title}>Confirmer ton adresse</h1>
            {verify.isSuccess ? (
              <>
                <Notice tone="success">
                  <p>C'est fait, ton adresse est vérifiée. Bienvenue sur le panneau !</p>
                </Notice>
                <Link to="/connexion">Se connecter</Link>
              </>
            ) : (
              <>
                <p className={styles.lead}>Un dernier clic, et ton compte est prêt.</p>
                <Button busy={verify.isPending} onClick={() => verify.mutate(token)}>
                  Confirmer mon adresse
                </Button>
              </>
            )}
          </div>
        ) : (
          <>
            {verify.isError && (
              <div className={styles.form}>
                <Notice tone="error">
                  <p>Ce lien n'est plus valable : il a déjà servi, ou il a expiré. Demande-en un nouveau.</p>
                </Notice>
              </div>
            )}
            <ResendForm />
          </>
        )}
      </Sheet>
    </main>
  )
}

export default VerifyPage
