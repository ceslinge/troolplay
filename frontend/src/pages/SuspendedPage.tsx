import { Link } from 'react-router'
import Button from '../components/Button'
import MyDecisions from '../components/MyDecisions'
import PageTitle from '../components/PageTitle'
import Sheet from '../components/Sheet'
import { useLogOut } from '../lib/useLeave'
import styles from './AuthPages.module.css'

/**
 * Ce que voit un compte suspendu, à la place de tout le site sauf les pages légales (#141) :
 * la décision, de quoi la contester une fois, et la déconnexion.
 */
function SuspendedPage({ until }: { until: string | null }) {
  const logout = useLogOut()
  const end = until
    ? `jusqu'au ${new Date(until).toLocaleString('fr-FR', { dateStyle: 'long', timeStyle: 'short' })}`
    : 'définitivement'

  return (
    <main className={`${styles.page} ${styles.wide}`}>
      <PageTitle>Compte suspendu</PageTitle>
      <Sheet seed="compte-suspendu" as="section">
        <div className={styles.form}>
          <h1 className={styles.title}>Ton compte est suspendu {end}</h1>
          <p className={styles.lead}>
            En attendant, le site t'est fermé. Tu peux lire la décision ci-dessous et la contester une fois : un membre de
            l'équipe relira et te répondra par mail. Les règles qui s'appliquent sont dans la{' '}
            <Link to="/moderation">charte de modération</Link>.
          </p>
          <div>
            <Button variant="secondary" busy={logout.isPending} onClick={() => logout.mutate()}>
              Se déconnecter
            </Button>
          </div>
        </div>
      </Sheet>
      <MyDecisions always />
    </main>
  )
}

export default SuspendedPage
