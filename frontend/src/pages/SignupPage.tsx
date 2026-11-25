import { useMutation } from '@tanstack/react-query'
import { type FormEvent, useState } from 'react'
import { Link } from 'react-router'
import { signUp } from '../api/accounts'
import { ApiError } from '../api/client'
import Button from '../components/Button'
import Field from '../components/Field'
import Notice from '../components/Notice'
import Sheet from '../components/Sheet'
import PageTitle from '../components/PageTitle'
import { RESUME_SHEET } from '../lib/next'
import { hasPendingDraft } from './characterForm'
import styles from './AuthPages.module.css'

function SignupPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [acceptRules, setAcceptRules] = useState(false)
  const [ageConfirmed, setAgeConfirmed] = useState(false)

  const signup = useMutation({ mutationFn: signUp })
  const error = signup.error instanceof ApiError ? signup.error : null

  function submit(event: FormEvent) {
    event.preventDefault()
    signup.mutate({ email, password, accept_rules: acceptRules, age_confirmed: ageConfirmed })
  }

  if (signup.isSuccess) {
    return (
      <main className={styles.page}>
        <PageTitle>Regarde tes emails</PageTitle>
        <Sheet seed="inscription-envoyee" as="section">
          <div className={styles.form}>
            <h1 className={styles.title}>Regarde tes emails</h1>
            <Notice tone="success">
              <p>{signup.data.detail}</p>
            </Notice>
            <p className={styles.lead}>
              Le lien est valable 24 heures. Il peut mettre quelques minutes à arriver : pense à regarder dans les
              indésirables.
            </p>
            {hasPendingDraft() && (
              <Notice>
                <p>
                  Ta fiche t'attend sur cet appareil. Ouvre le lien de vérification ici, ou reviens sur cet appareil ensuite
                  pour l'épingler.
                </p>
              </Notice>
            )}
            <Link to="/verifier">Rien reçu ? Demander un nouveau lien</Link>
          </div>
        </Sheet>
      </main>
    )
  }

  return (
    <main className={styles.page}>
      <PageTitle>Créer un compte</PageTitle>
      <Sheet seed="inscription" as="section">
        <form className={styles.form} onSubmit={submit} noValidate>
          <h1 className={styles.title}>Épingler ses personnages</h1>
          <p className={styles.lead}>Un compte, et tous tes personnages derrière. Personne ne verra qu'ils sont à toi.</p>
          {error && error.status !== 422 && (
            <Notice tone="error">
              <p>{error.message}</p>
            </Notice>
          )}
          <Field label="Adresse email" name="email" type="email" value={email} onChange={setEmail} autoComplete="email" required error={error?.fields.email} />
          <Field
            label="Mot de passe"
            name="password"
            type="password"
            value={password}
            onChange={setPassword}
            autoComplete="new-password"
            required
            hint="10 caractères au moins. Une phrase fait très bien l'affaire."
            error={error?.fields.password}
          />
          <div>
            <label className={styles.check}>
              <input type="checkbox" checked={acceptRules} onChange={(event) => setAcceptRules(event.target.checked)} />
              <span>
                J'ai lu et j'accepte les <Link to="/regles">règles d'usage</Link>. Ce qu'on garde de toi est expliqué
                dans la page <Link to="/confidentialite">confidentialité</Link>.
              </span>
            </label>
            {error?.fields.accept_rules && <span className={styles.error}>{error.fields.accept_rules}</span>}
          </div>
          <div>
            <label className={styles.check}>
              <input type="checkbox" checked={ageConfirmed} onChange={(event) => setAgeConfirmed(event.target.checked)} />
              <span>J'ai au moins 18 ans.</span>
            </label>
            {error?.fields.age_confirmed && <span className={styles.error}>{error.fields.age_confirmed}</span>}
          </div>
          <Button type="submit" busy={signup.isPending}>
            Créer mon compte
          </Button>
          <div className={styles.links}>
            <Link to={hasPendingDraft() ? `/connexion?suite=${encodeURIComponent(RESUME_SHEET)}` : '/connexion'}>
              Déjà un compte ? Se connecter
            </Link>
          </div>
        </form>
      </Sheet>
    </main>
  )
}

export default SignupPage
