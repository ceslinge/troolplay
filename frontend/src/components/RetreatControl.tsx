import { useMutation, useQueryClient } from '@tanstack/react-query'
import { type FormEvent, useState } from 'react'
import { type Character, updateCharacter } from '../api/characters'
import { useToast } from '../lib/toast'
import Button from './Button'
import Field from './Field'
import styles from './RetreatControl.module.css'

/**
 * Mettre son personnage en pause, ou le faire revenir : un geste rapide, pas un formulaire.
 * Seul le propriétaire le voit (la fiche le pose sous is_mine).
 */
function RetreatControl({ character }: { character: Character }) {
  const [asking, setAsking] = useState(false)
  const [note, setNote] = useState('')
  const queryClient = useQueryClient()
  const toast = useToast()

  const change = useMutation({
    mutationFn: (inactive: boolean) =>
      updateCharacter(character.id, inactive ? { inactive, inactive_note: note.trim() || null } : { inactive }),
    onSuccess: async (_, inactive) => {
      // La fiche, l'annuaire, Mon compte et l'accueil changent tous.
      await queryClient.invalidateQueries({ queryKey: ['character', String(character.id)] })
      await queryClient.invalidateQueries({ queryKey: ['characters'] })
      await queryClient.invalidateQueries({ queryKey: ['home'] })
      setAsking(false)
      setNote('')
      toast.show(inactive ? `${character.name} se met en retrait.` : `${character.name} est de retour !`, 'success')
    },
    onError: (failure) => toast.show(`Pas changé : ${failure.message}`, 'error'),
  })

  if (character.inactive) {
    return (
      <Button variant="secondary" busy={change.isPending} onClick={() => change.mutate(false)}>
        Faire revenir {character.name}
      </Button>
    )
  }

  if (!asking) {
    return (
      <Button variant="secondary" onClick={() => setAsking(true)}>
        Mettre en retrait
      </Button>
    )
  }

  function submit(event: FormEvent) {
    event.preventDefault()
    change.mutate(true)
  }

  return (
    <form className={styles.form} onSubmit={submit}>
      <p className="hint">
        {character.name} quittera les listes, mais sa fiche restera lisible. Un clic suffira pour revenir.
      </p>
      <Field
        label="Une raison, côté RP ? (facultatif)"
        name="inactive_note"
        value={note}
        onChange={setNote}
        maxLength={200}
        hint="Un voyage en mer, une mort glorieuse à Bonta… Une pause comme une fin : on peut toujours revenir."
      />
      <div className={styles.actions}>
        <Button variant="secondary" onClick={() => setAsking(false)}>
          Annuler
        </Button>
        <Button type="submit" busy={change.isPending}>
          Mettre en retrait
        </Button>
      </div>
    </form>
  )
}

export default RetreatControl
