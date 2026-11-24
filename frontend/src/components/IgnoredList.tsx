import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router'
import { type CharacterSummary, fetchIgnored } from '../api/characters'
import { useIgnore } from '../lib/useIgnore'
import Button from './Button'
import Seal from './Seal'
import Sheet from './Sheet'
import styles from './IgnoredList.module.css'

function Row({ character }: { character: CharacterSummary }) {
  const { unignore } = useIgnore(character.id, character.name)
  return (
    <li className={styles.row}>
      <span className={styles.who}>
        <Seal name={character.name} />
        <Link to={`/personnages/${character.id}`}>{character.name}</Link>
        {character.server && <span className={styles.server}>{character.server.name}</span>}
      </span>
      <Button variant="secondary" busy={unignore.isPending} onClick={() => unignore.mutate()}>
        Ne plus ignorer
      </Button>
    </li>
  )
}

/** Dans Mon compte : les personnages que j'ignore, pour revenir en arrière. Rien s'il n'y en a pas. */
function IgnoredList() {
  const ignored = useQuery({ queryKey: ['ignored'], queryFn: fetchIgnored })
  if (!ignored.data?.length) return null
  return (
    <section className={styles.section}>
      <h2 className={styles.title}>Personnages ignorés</h2>
      <Sheet seed="compte-ignores" contentClassName={styles.card}>
        <p className={styles.hint}>Ils n'apparaissent plus dans tes listes. Personne d'autre ne le sait.</p>
        <ul className={styles.list}>
          {ignored.data.map((c) => (
            <Row key={c.id} character={c} />
          ))}
        </ul>
      </Sheet>
    </section>
  )
}

export default IgnoredList
