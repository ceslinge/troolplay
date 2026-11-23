import { Link } from 'react-router'
import { MAX_CHARACTERS } from '../api/characters'
import { setActiveCharacter, useActiveCharacter, useMyCharacters } from '../lib/activeCharacter'
import styles from './CharacterRail.module.css'
import Seal from './Seal'

/**
 * La barre de ses personnages : un sceau par personnage pour passer de l'un à l'autre,
 * et un « + » pour en présenter un nouveau. Rien tant qu'on n'en a aucun.
 */
function CharacterRail() {
  const mine = useMyCharacters()
  const active = useActiveCharacter()
  if (!mine || mine.length === 0) {
    return null
  }

  return (
    <nav className={styles.rail} aria-label="Mes personnages">
      <ul className={styles.list}>
        {mine.map((c) => {
          // Un personnage masqué ou en retrait reste là, mais plus pâle.
          const state = c.hidden ? 'masqué' : c.inactive ? 'en retrait' : null
          return (
            <li key={c.id}>
              <Link
                to={`/personnages/${c.id}`}
                className={`${styles.item} ${state ? styles.faded : ''}`}
                aria-current={c.id === active?.id ? 'true' : undefined}
                onClick={() => setActiveCharacter(c.id)}
              >
                <Seal name={c.name} size="md" />
                <span className={styles.name}>
                  {c.name}
                  {state && <span className={styles.state}> ({state})</span>}
                </span>
              </Link>
            </li>
          )
        })}
        {/* Le « + » disparaît une fois le maximum atteint. */}
        {mine.length < MAX_CHARACTERS && (
          <li>
            <Link to="/personnages/nouveau" className={`${styles.item} ${styles.add}`}>
              <span className={styles.plus} aria-hidden="true">
                +
              </span>
              <span className={`${styles.name} ${styles.addName}`}>Présenter un nouveau personnage</span>
            </Link>
          </li>
        )}
      </ul>
    </nav>
  )
}

export default CharacterRail
