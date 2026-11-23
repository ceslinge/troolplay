import { Link } from 'react-router'
import type { Place } from '../api/servers'
import { CLASS_LABELS } from '../lib/classes'
import { formatSchedule } from '../lib/schedule'
import CopyButton from './CopyButton'
import Medallion from './Medallion'
import styles from './PlaceCard.module.css'
import Seal from './Seal'
import Sheet from './Sheet'

/** Un lieu du panneau « Qui traîne ici ? », avec ses habitués. */
function PlaceCard({ place }: { place: Place }) {
  const count = place.regulars.length
  const coordinates = `${place.x},${place.y}`

  return (
    <Sheet as="section" pinned seed={`lieu-${place.area}-${coordinates}`} contentClassName={styles.card}>
      <div className={styles.head}>
        <Medallion icon="pin" />
        <div className={styles.title}>
          <h2 className={styles.name}>{place.label ?? place.area}</h2>
          <span className={styles.where}>
            {place.label && `${place.area} `}[{place.x}, {place.y}]
            <CopyButton text={coordinates} label={`Copier les coordonnées de ${place.label ?? place.area}`} />
          </span>
        </div>
        <span className={styles.count}>
          {count} habitué{count > 1 ? 's' : ''}
        </span>
      </div>
      <ul className={styles.regulars}>
        {place.regulars.map(({ character: c, habits }) => {
          const schedule = formatSchedule(c.play_days, c.play_periods)
          const facts = [c.class && CLASS_LABELS[c.class], schedule].filter(Boolean).join(' · ')
          return (
            <li key={c.id} className={styles.regular}>
              <Seal name={c.name} />
              <div className={styles.who}>
                <Link to={`/personnages/${c.id}`} className={styles.link}>
                  {c.name}
                </Link>
                {facts && <span className={styles.facts}>{facts}</span>}
                {habits && <span className={styles.habits}>{habits}</span>}
              </div>
            </li>
          )
        })}
      </ul>
    </Sheet>
  )
}

export default PlaceCard
