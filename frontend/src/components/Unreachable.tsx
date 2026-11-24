import { useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import Button from './Button'
import StatusPage from './StatusPage'

/** Le serveur ne répond pas : on le dit, plutôt qu'une page vide ou une redirection trompeuse. */
function Unreachable() {
  const queryClient = useQueryClient()
  const [busy, setBusy] = useState(false)

  async function retry() {
    setBusy(true)
    // Seules les demandes qui ont échoué repartent.
    await queryClient.refetchQueries({ predicate: (query) => query.state.status === 'error' })
    setBusy(false)
  }

  return (
    <StatusPage
      tab="Panneau inaccessible"
      icon="chain"
      title="Le panneau ne répond pas"
      lead="Le site n'arrive pas à joindre son serveur pour l'instant. Ce n'est pas de ton fait : réessaie dans un moment."
    >
      <Button busy={busy} onClick={retry}>
        Réessayer
      </Button>
    </StatusPage>
  )
}

export default Unreachable
