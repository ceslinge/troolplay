import { useEffect, useState } from 'react'
import { useParams } from 'react-router'
import { type Character, fetchCharacter } from '../api/characters'
import CopyButton from '../components/CopyButton'
import type { IconName } from '../components/Icon'
import Medallion from '../components/Medallion'
import Seal from '../components/Seal'
import Section from '../components/Section'
import Sheet from '../components/Sheet'
import { agree } from '../lib/agree'
import { formatSchedule } from '../lib/schedule'
import styles from './CharacterPage.module.css'

type State =
  | { status: 'loading' }
  | { status: 'not-found' }
  | { status: 'error' }
  | { status: 'ready'; character: Character; age: number }

type SectionData = {
  id: string
  icon: IconName
  title: string
  text: string | null
  tone?: 'rumor'
}

function sectionsOf(c: Character): SectionData[] {
  const sections: SectionData[] = [
    {
      id: 'apparence',
      icon: 'eye',
      title: agree(c.gender, {
        feminine: 'À quoi on la reconnaît',
        masculine: 'À quoi on le reconnaît',
        neutral: 'À quoi on reconnaît ce personnage',
      }),
      text: c.appearance,
    },
    { id: 'caractere', icon: 'mask', title: 'Son caractère', text: c.personality },
    {
      id: 'histoire',
      icon: 'path',
      title: agree(c.gender, { feminine: "D'où elle vient", masculine: "D'où il vient", neutral: 'Son histoire' }),
      text: c.backstory,
    },
    {
      id: 'quete',
      icon: 'compass',
      title: agree(c.gender, {
        feminine: "Ce qu'elle cherche",
        masculine: "Ce qu'il cherche",
        neutral: 'Ce que ce personnage cherche',
      }),
      text: c.goals,
    },
    {
      id: 'failles',
      icon: 'chain',
      title: agree(c.gender, { feminine: 'Ce qui la perdra', masculine: 'Ce qui le perdra', neutral: 'Ses failles' }),
      text: c.flaws,
    },
    { id: 'rumeurs', icon: 'bubbles', title: "Ce qu'on raconte au comptoir", text: c.rumors, tone: 'rumor' },
  ]
  return sections.filter((section) => section.text)
}

/** De 0 à 1 : une fiche jaunit sur deux ans. */
function ageOf(character: Character): number {
  const twoYears = 2 * 365 * 24 * 3600 * 1000
  return (Date.now() - Date.parse(character.created_at)) / twoYears
}

function CharacterPage() {
  const { id = '' } = useParams()
  const [state, setState] = useState<State>({ status: 'loading' })

  useEffect(() => {
    let ignore = false
    fetchCharacter(id)
      .then((character) => {
        if (!ignore) {
          setState(character ? { status: 'ready', character, age: ageOf(character) } : { status: 'not-found' })
        }
      })
      .catch(() => {
        if (!ignore) {
          setState({ status: 'error' })
        }
      })
    return () => {
      ignore = true
    }
  }, [id])

  if (state.status !== 'ready') {
    const messages = {
      loading: 'On cherche la fiche…',
      'not-found': 'Personne ne répond à ce nom sur le panneau.',
      error: "Le panneau est inaccessible pour l'instant. Réessaie dans un moment.",
    }
    return (
      <main className={styles.page}>
        <Sheet>
          <p className={styles.message}>{messages[state.status]}</p>
        </Sheet>
      </main>
    )
  }

  const { character: c, age } = state
  const sections = sectionsOf(c)
  const schedule = formatSchedule(c.play_days, c.play_periods)
  const meta = [c.class, c.level && `niveau ${c.level}`, c.server?.name].filter(Boolean).join(' · ')
  const findTitle = agree(c.gender, {
    feminine: 'La retrouver en jeu',
    masculine: 'Le retrouver en jeu',
    neutral: 'Croiser ce personnage en jeu',
  })

  return (
    <main className={styles.page}>
      <Sheet as="section" contentClassName={styles.header} seed={`${c.id}-entete`} age={age}>
        <div className={styles.portrait}>
          <span className={styles.avatar} aria-hidden="true">
            {c.name.slice(0, 2).toUpperCase()}
          </span>
          <span className={styles.seal}>
            <Seal name={c.name} size="lg" />
          </span>
        </div>
        <div className={styles.identity}>
          {meta && <span className={styles.meta}>{meta}</span>}
          <h1 className={styles.name}>{c.name}</h1>
          {c.inactive && (
            <span className={styles.inactive}>En retrait{c.inactive_note && ` : ${c.inactive_note}`}</span>
          )}
          {c.hook && (
            <>
              <blockquote className={styles.hook}>« {c.hook} »</blockquote>
              <span className={styles.meta}>
                {agree(c.gender, {
                  feminine: "Ce qu'elle répond, en général, quand on l'aborde",
                  masculine: "Ce qu'il répond, en général, quand on l'aborde",
                  neutral: 'Sa réponse habituelle quand on vient lui parler',
                })}
              </span>
            </>
          )}
        </div>
      </Sheet>

      {sections.length > 0 && (
        <nav className={styles.summary} aria-label="Sections de la fiche">
          {sections.map((section) => (
            <a key={section.id} href={`#${section.id}`} title={section.title} aria-label={section.title}>
              <Medallion icon={section.icon} />
            </a>
          ))}
          <a href="#en-jeu" title={findTitle} aria-label={findTitle}>
            <Medallion icon="pin" />
          </a>
        </nav>
      )}

      <div className={styles.columns}>
        {sections.length > 0 && (
          <Sheet
            as="article"
            className={styles.storySheet}
            contentClassName={styles.story}
            seed={`${c.id}-histoire`}
            age={age}
          >
            {sections.map((section) => (
              <Section key={section.id} id={section.id} icon={section.icon} title={section.title} tone={section.tone}>
                <p>{section.text}</p>
              </Section>
            ))}
          </Sheet>
        )}

        <aside className={styles.aside}>
          <Sheet variant="marked" as="section" seed={`${c.id}-en-jeu`} age={age}>
            <div id="en-jeu" className={styles.findTitle}>
              <Medallion icon="pin" />
              <h2>{findTitle}</h2>
            </div>
            <dl className={styles.facts}>
              {c.ingame_name && (
                <div>
                  <dt>Nom en jeu</dt>
                  <dd className={styles.copyRow}>
                    <strong>{c.ingame_name}</strong>
                    <CopyButton text={c.ingame_name} label="Copier le nom en jeu" />
                  </dd>
                </div>
              )}
              {c.hangouts.length > 0 && (
                <div>
                  <dt>Où</dt>
                  {c.hangouts.map((h) => (
                    <dd key={h.id}>
                      {h.label ? `${h.label}, ` : ''}
                      {h.area} [{h.x}, {h.y}]{h.habits && <span className={styles.habits}>{h.habits}</span>}
                    </dd>
                  ))}
                </div>
              )}
              {schedule && (
                <div>
                  <dt>Quand</dt>
                  <dd>{schedule}</dd>
                </div>
              )}
            </dl>
            {!c.ingame_name && c.hangouts.length === 0 && !schedule && (
              <p className={styles.message}>Pas encore d'indication. Un mot en jeu, peut-être ?</p>
            )}
          </Sheet>

          {c.ooc_note && (
            <Sheet variant="muted" seed={`${c.id}-hrp`} age={age}>
              <h2 className={styles.oocTitle}>Un mot hors RP</h2>
              <p className={styles.ooc}>{c.ooc_note}</p>
            </Sheet>
          )}
        </aside>
      </div>
    </main>
  )
}

export default CharacterPage
