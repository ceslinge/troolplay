import { useMutation, useQueryClient } from '@tanstack/react-query'
import { type MyCharacter, orderMyCharacters } from '../api/characters'
import { useToast } from '../lib/toast'
import styles from './CharacterOrder.module.css'
import Seal from './Seal'

type Props = { characters: MyCharacter[] }

/**
 * Ranger ses personnages, dans l'ordre de la barre. Des boutons plutôt qu'un glisser-déposer :
 * ils marchent au doigt, au clavier et avec un lecteur d'écran. Chaque déplacement est enregistré aussitôt.
 */
function CharacterOrder({ characters }: Props) {
  const queryClient = useQueryClient()
  const toast = useToast()
  const key = ['characters', 'mine']
  const save = useMutation({
    mutationFn: (list: MyCharacter[]) => orderMyCharacters(list.map((c) => c.id)),
    // La liste bouge tout de suite, sans attendre le serveur.
    onMutate: async (list) => {
      await queryClient.cancelQueries({ queryKey: key })
      const before = queryClient.getQueryData<MyCharacter[]>(key)
      queryClient.setQueryData(key, list)
      return { before }
    },
    onError: (failure, _list, context) => {
      queryClient.setQueryData(key, context?.before)
      toast.show(`Ordre pas enregistré : ${failure.message}`, 'error')
    },
    onSettled: () => queryClient.invalidateQueries({ queryKey: key }),
  })

  // Ceux qu'on ne joue pas (en retrait, masqués) sont rangés à part, après les autres : on range chaque groupe en lui-même.
  const resting = (c: MyCharacter) => c.inactive || c.hidden
  const canMove = (index: number, by: -1 | 1) => {
    const target = index + by
    return target >= 0 && target < characters.length && resting(characters[target]) === resting(characters[index])
  }

  function move(index: number, by: -1 | 1) {
    const target = index + by
    if (!canMove(index, by)) return
    const list = [...characters]
    ;[list[index], list[target]] = [list[target], list[index]]
    save.mutate(list)
  }

  return (
    <ol className={styles.list}>
      {characters.map((c, index) => (
        <li key={c.id} className={styles.row}>
          <span className={styles.rank} aria-hidden="true">
            {index + 1}
          </span>
          <Seal name={c.name} />
          <span className={styles.name}>
            {c.name}
            {resting(c) && <span className={styles.state}> ({c.hidden ? 'masqué' : 'en retrait'})</span>}
          </span>
          {/* aria-disabled plutôt que disabled : le bouton garde le focus quand il arrive au bout. */}
          <button
            type="button"
            className={styles.move}
            aria-label={`Monter ${c.name}`}
            aria-disabled={!canMove(index, -1)}
            onClick={() => move(index, -1)}
          >
            ↑
          </button>
          <button
            type="button"
            className={styles.move}
            aria-label={`Descendre ${c.name}`}
            aria-disabled={!canMove(index, 1)}
            onClick={() => move(index, 1)}
          >
            ↓
          </button>
        </li>
      ))}
    </ol>
  )
}

export default CharacterOrder
