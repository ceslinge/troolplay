import { useQuery } from '@tanstack/react-query'
import { type ReactNode, type RefObject, useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router'
import { ApiError } from '../api/client'
import { fetchStory, type Story } from '../api/stories'
import MembersOnly from '../components/MembersOnly'
import PageTitle from '../components/PageTitle'
import ReportButton from '../components/ReportButton'
import Seal from '../components/Seal'
import Sheet from '../components/Sheet'
import TeamBox from '../components/TeamBox'
import StoryText from '../components/StoryText'
import Unreachable from '../components/Unreachable'
import { readingLabel, readingMinutes, storyDate, WARNING_LABELS } from '../lib/stories'
import { useMe } from '../lib/useMe'
import styles from './StoryPage.module.css'
import { ofName } from '../lib/text'

/** Une fine barre en haut de l'écran : où l'on en est dans un long texte. */
function ReadingProgress({ target }: { target: RefObject<HTMLElement | null> }) {
  const [progress, setProgress] = useState(0)
  useEffect(() => {
    function measure() {
      const el = target.current
      if (!el) return
      const { top, height } = el.getBoundingClientRect()
      const span = height - window.innerHeight
      setProgress(span <= 0 ? 1 : Math.min(1, Math.max(0, -top / span)))
    }
    measure()
    window.addEventListener('scroll', measure, { passive: true })
    window.addEventListener('resize', measure)
    return () => {
      window.removeEventListener('scroll', measure)
      window.removeEventListener('resize', measure)
    }
  }, [target])
  return <div className={styles.progress} style={{ transform: `scaleX(${progress})` }} aria-hidden="true" />
}

function Reading({ story }: { story: Story }) {
  const text = useRef<HTMLElement>(null)
  // L'auteur sait ce qu'il a écrit : seul le lecteur passe par l'avertissement.
  const [revealed, setRevealed] = useState(story.is_mine || story.content_warnings.length === 0)
  const c = story.character

  return (
    <>
      <ReadingProgress target={text} />
      <Sheet as="article" seed={`histoire-${story.id}`} contentClassName={styles.sheet}>
        <header className={styles.header}>
          {(!story.published || story.hidden) && (
            <p className={styles.state}>
              {story.hidden ? 'Masquée par la modération : toi seul la vois.' : 'Brouillon : toi seul le vois.'}
            </p>
          )}
          <h1 className={styles.title}>{story.title}</h1>
          <p className={styles.meta}>
            {c ? (
              <>
                <Seal name={c.name} />
                <Link to={`/personnages/${c.id}`} className={styles.character}>
                  {c.name}
                </Link>
                {c.server && <span>sur {c.server.name}</span>}
              </>
            ) : (
              <span>Un personnage qui a quitté le panneau</span>
            )}
            <span aria-hidden="true">·</span>
            {story.published_at && <span>{storyDate(story.published_at)}</span>}
            <span aria-hidden="true">·</span>
            <span>{readingLabel(readingMinutes(story.body))}</span>
          </p>
          {story.is_mine && (
            <Link to={`/histoires/${story.id}/modifier`} className={styles.edit}>
              Modifier mon histoire
            </Link>
          )}
        </header>

        {story.content_warnings.length > 0 && (
          <div className={styles.warning} role="note">
            <p>
              <strong>Avertissement :</strong> {story.content_warnings.map((w) => WARNING_LABELS[w]).join(', ')}.
              {story.content_note && <> {story.content_note}</>}
            </p>
            {!revealed && (
              <button type="button" className={styles.reveal} onClick={() => setRevealed(true)}>
                Lire quand même
              </button>
            )}
          </div>
        )}

        {revealed && (
          <section ref={text} className={styles.text} aria-label="L'histoire">
            <StoryText body={story.body} />
          </section>
        )}

        {revealed && story.author_note && (
          <aside className={styles.note} aria-label="Mot de l'auteur">
            <span className={styles.noteLabel}>Mot de l'auteur, hors RP</span>
            <p>{story.author_note}</p>
          </aside>
        )}

        {story.published && (
          <div className={styles.report}>
            <ReportButton target="story" targetId={story.id} mine={story.is_mine} />
          </div>
        )}
        <div className={styles.report}>
          <TeamBox target="story" id={story.id} />
        </div>
      </Sheet>
      {c && (
        <p className={styles.back}>
          <Link to={`/personnages/${c.id}`}>Les autres histoires {ofName(c.name)}</Link>
          {/* Un serveur fermé n'a plus de page Communauté. */}
          {c.server && !c.server.closed && <Link to={`/communaute/${c.server.id}/histoires`}>Les histoires {ofName(c.server.name)}</Link>}
        </p>
      )}
    </>
  )
}

/** /histoires/:id : une histoire, pour la lire tranquillement. */
function StoryPage() {
  const { id = '' } = useParams()
  const me = useMe()
  const story = useQuery({ queryKey: ['story', Number(id)], queryFn: () => fetchStory(Number(id)), enabled: Boolean(me.data) })

  const main = (title: string, content: ReactNode) => (
    <main className={styles.page}>
      <PageTitle>{title}</PageTitle>
      {content}
    </main>
  )

  if (me.isError) return <Unreachable />
  if (me.isPending) return null
  if (!me.data) return main('Une histoire', <MembersOnly />)
  if (story.isPending) return null
  if (story.isError) {
    if (story.error instanceof ApiError && story.error.status === 404) {
      return main('Histoire introuvable', <p className={styles.missing}>Cette histoire n'est pas sur le panneau, ou plus.</p>)
    }
    return <Unreachable />
  }
  return main(story.data.title, <Reading key={story.data.id} story={story.data} />)
}

export default StoryPage
