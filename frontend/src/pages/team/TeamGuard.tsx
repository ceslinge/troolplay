import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router'
import type { Capability } from '../../api/accounts'
import StatusPage from '../../components/StatusPage'
import Unreachable from '../../components/Unreachable'
import { useMe } from '../../lib/useMe'

/** L'Espace équipe ne s'ouvre qu'à qui a la capacité : les autres sont refusés, poliment. */
function TeamGuard({ capability = 'moderate', children }: { capability?: Capability; children: ReactNode }) {
  const me = useMe()
  const { pathname } = useLocation()
  if (me.isError) return <Unreachable />
  if (me.isPending) return null
  if (!me.data) return <Navigate to={`/connexion?suite=${encodeURIComponent(pathname)}`} replace />
  if (!me.data.capabilities.includes(capability)) {
    return (
      <StatusPage tab="Réservé à l'équipe" icon="crossed" title="Cette page est réservée à l'équipe" lead="Elle sert aux modérateurs et aux admins du panneau.">
        <a href="/">Retour à l'accueil</a>
      </StatusPage>
    )
  }
  return <>{children}</>
}

export default TeamGuard
