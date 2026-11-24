import { Link } from 'react-router'
import type { StorySummary } from '../api/stories'
import { readingLabel, storyDate, WARNING_LABELS } from '../lib/stories'
import Seal from './Seal'
import Sheet from './Sheet'
import styles from './StoryCard.module.css'

type Props = {
  story: StorySummary
  /** Sur la fiche d'un personnage, inutile de répéter qui signe. */
  showCharacter?: boolean
}

/** Une histoire dans une liste : de quoi choisir avant de l'ouvrir. */
function StoryCard({ story, showCharacter = true }: Props) {
  const warned = story.content_warnings.length > 0
  return (
    <Sheet as="article" seed={`histoire-${story.id}-carte`} contentClassName={styles.card}>
      <h3 className={styles.title}>
        <Link to={`/histoires/${story.id}`}>{story.title}</Link>
      </h3>
      <p className={styles.meta}>
        {showCharacter && story.character && (
          <>
            <Seal name={story.character.name} />
            <Link to={`/personnages/${story.character.id}`} className={styles.character}>
              {story.character.name}
            </Link>
            {' · '}
          </>
        )}
        {story.published_at && storyDate(story.published_at)} · {readingLabel(story.reading_minutes)}
      </p>
      {warned ? (
        <p className={styles.warning}>
          <strong>Avertissement :</strong> {story.content_warnings.map((w) => WARNING_LABELS[w]).join(', ')}
          {story.content_note && <> · {story.content_note}</>}
        </p>
      ) : (
        story.excerpt && <p className={styles.excerpt}>{story.excerpt}</p>
      )}
    </Sheet>
  )
}

export default StoryCard
