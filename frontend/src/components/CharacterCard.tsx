import { Link } from 'react-router'
import type { CharacterSummary } from '../api/characters'
import { CLASS_LABELS } from '../lib/classes'
import { formatSchedule } from '../lib/schedule'
import styles from './CharacterCard.module.css'
import Seal from './Seal'
import Sheet from './Sheet'

type Props = {
  character: CharacterSummary
}

/** Un personnage dans une liste : de quoi donner envie d'ouvrir sa fiche. */
function CharacterCard({ character: c }: Props) {
  const facts = [c.class && CLASS_LABELS[c.class], c.level && `niv. ${c.level}`].filter(Boolean).join(' · ')
  const schedule = formatSchedule(c.play_days, c.play_periods)

  return (
    <Link to={`/personnages/${c.id}`} className={styles.link}>
      <Sheet as="article" seed={`${c.id}-carte`} contentClassName={styles.card}>
        <div className={styles.head}>
          <Seal name={c.name} />
          <div className={styles.identity}>
            <h3 className={styles.name}>{c.name}</h3>
            {facts && <span className={styles.facts}>{facts}</span>}
          </div>
        </div>
        {c.hook && <p className={styles.hook}>« {c.hook} »</p>}
        {schedule && <p className={styles.schedule}>{schedule}</p>}
        {c.inactive && <span className={styles.inactive}>En retrait</span>}
      </Sheet>
    </Link>
  )
}

export default CharacterCard
