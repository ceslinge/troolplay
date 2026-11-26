import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router'
import { fetchMyStories, MAX_DRAFTS, type MyStorySummary } from '../api/stories'
import Notice from './Notice'
import Sheet from './Sheet'
import styles from './MyStories.module.css'

function state(story: MyStorySummary): string {
  if (story.hidden) return 'Masquée par la modération'
  return story.published ? 'Publiée' : 'Brouillon'
}

/** Mes histoires, brouillons compris, la dernière modifiée d'abord : pour Mon compte. */
function MyStories() {
  const stories = useQuery({ queryKey: ['stories', 'mine'], queryFn: fetchMyStories })
  const drafts = stories.data?.filter((s) => !s.published).length ?? 0

  return (
    <section className={styles.section}>
      <div className={`paper-tag ${styles.head}`}>
        <h2 className={styles.title}>Mes histoires</h2>
        {drafts >= MAX_DRAFTS ? (
          <span className={styles.note}>
            {MAX_DRAFTS} brouillons : publie ou supprime-en un pour en commencer un autre.
          </span>
        ) : (
          <Link to="/histoires/nouvelle">Écrire une histoire</Link>
        )}
      </div>
      {stories.isPending ? null : stories.isError ? (
        <Notice tone="error">
          <p>Impossible de charger tes histoires pour l'instant.</p>
        </Notice>
      ) : stories.data.length === 0 ? (
        <Notice>
          <p>Pas encore d'histoire. Ce que tes personnages ont vécu en jeu mérite peut-être d'être raconté.</p>
        </Notice>
      ) : (
        <Sheet seed="compte-histoires" contentClassName={styles.list}>
          <ul>
            {stories.data.map((story) => (
              <li key={story.id} className={styles.item}>
                <Link to={`/histoires/${story.id}/modifier`} className={styles.link}>
                  {story.title}
                </Link>
                <span className={styles.meta}>
                  {story.character ? story.character.name : 'Sans signature'} ·{' '}
                  <span className={story.published && !story.hidden ? styles.published : undefined}>{state(story)}</span> ·
                  modifiée le {new Date(story.updated_at).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long' })}
                </span>
              </li>
            ))}
          </ul>
        </Sheet>
      )}
    </section>
  )
}

export default MyStories
