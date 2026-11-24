import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link } from 'react-router'
import { fetchTeamContent, setHidden, type Target } from '../api/moderation'
import { useCan } from '../lib/useCan'
import { useToast } from '../lib/toast'
import Button from './Button'
import ReasonForm from './ReasonForm'
import styles from './TeamBox.module.css'

/** Sur une fiche ou une histoire, pour l'équipe seulement : agir sans passer par un signalement. */
function TeamBox({ target, id }: { target: Target; id: number }) {
  const canModerate = useCan('moderate')
  const queryClient = useQueryClient()
  const toast = useToast()
  const [acting, setActing] = useState(false)
  const info = useQuery({ queryKey: ['moderation', 'content', target, id], queryFn: () => fetchTeamContent(target, id), enabled: canModerate })
  const hide = useMutation({
    mutationFn: (reason: string) => setHidden(target, id, !info.data!.hidden, reason),
    onSuccess: async (r) => {
      toast.show(r.detail, 'success')
      setActing(false)
      await queryClient.invalidateQueries()
    },
  })

  if (!canModerate || !info.data) return null
  const c = info.data
  const slug = target === 'character' ? 'personnage' : 'histoire'

  return (
    <aside className={styles.box} aria-label="Équipe">
      <span className={styles.label}>Équipe</span>
      <p className={styles.line}>
        {c.owner ? <Link to={`/equipe/comptes/${c.owner.id}`}>Compte n°{c.owner.id}</Link> : 'Un PNJ'}
        {c.hidden && ' · masqué'}
        {c.open_reports > 0 && (
          <>
            {' · '}
            <Link to={`/equipe/signalements/${slug}/${id}`}>
              {c.open_reports} signalement{c.open_reports > 1 ? 's' : ''} en attente
            </Link>
          </>
        )}
      </p>
      {acting ? (
        <ReasonForm
          title={c.hidden ? 'Rétablir' : 'Masquer'}
          confirm={c.hidden ? 'Rétablir' : 'Masquer'}
          danger={!c.hidden}
          busy={hide.isPending}
          error={hide.error}
          onConfirm={(reason) => hide.mutate(reason)}
          onCancel={() => setActing(false)}
        />
      ) : (
        <div>
          <Button variant={c.hidden ? 'secondary' : 'danger'} onClick={() => setActing(true)}>
            {c.hidden ? 'Rétablir' : 'Masquer'}
          </Button>
        </div>
      )}
    </aside>
  )
}

export default TeamBox
