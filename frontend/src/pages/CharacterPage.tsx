import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router'
import { type Character, fetchCharacter } from '../api/characters'
import CopyButton from '../components/CopyButton'
import type { IconName } from '../components/Icon'
import Medallion from '../components/Medallion'
import RetreatControl from '../components/RetreatControl'
import Seal from '../components/Seal'
import Section from '../components/Section'
import { IgnoreButton, IgnoredBanner } from '../components/IgnoreControl'
import ReportButton from '../components/ReportButton'
import Sheet from '../components/Sheet'
import StoryList from '../components/StoryList'
import TeamBox from '../components/TeamBox'
import { agree } from '../lib/agree'
import { CLASS_LABELS } from '../lib/classes'
import { formatSchedule } from '../lib/schedule'
import PageTitle from '../components/PageTitle'
import styles from './CharacterPage.module.css'

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
  const query = useQuery({
    queryKey: ['character', id],
    queryFn: async () => {
      const character = await fetchCharacter(id)
      // L'âge se calcule au chargement : l'affichage doit rester pur.
      return character && { character, age: ageOf(character) }
    },
  })
  if (query.isPending || query.isError || !query.data) {
    const message = query.isPending
      ? 'On cherche la fiche…'
      : query.isError
        ? "Le panneau est inaccessible pour l'instant. Réessaie dans un moment."
        : 'Personne ne répond à ce nom sur le panneau.'
    return (
      <main className={styles.page}>
        <PageTitle>Fiche introuvable</PageTitle>
        <Sheet>
          <p className={styles.message}>{message}</p>
        </Sheet>
      </main>
    )
  }

  const { character: c, age } = query.data
  const sections = sectionsOf(c)
  const schedule = formatSchedule(c.play_days, c.play_periods)
  const meta = c.server ? `Sur ${c.server.name}${c.server.closed ? ' (serveur fermé)' : ''}` : null
  const findTitle = agree(c.gender, {
    feminine: 'La retrouver en jeu',
    masculine: 'Le retrouver en jeu',
    neutral: 'Croiser ce personnage en jeu',
  })

  return (
    <main className={styles.page}>
      <PageTitle>{c.name}</PageTitle>
      <IgnoredBanner character={c} />
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
          {c.is_mine && (
            <div className={styles.ownerActions}>
              <Link to={`/personnages/${c.id}/modifier`} className={styles.edit}>
                Modifier ma fiche
              </Link>
              <RetreatControl character={c} />
            </div>
          )}
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

      <nav className={`paper-tag ${styles.summary}`} aria-label="Sections de la fiche">
        {sections.map((section) => (
          <a key={section.id} href={`#${section.id}`} title={section.title} aria-label={section.title}>
            <Medallion icon={section.icon} />
          </a>
        ))}
        <a href="#en-jeu" title={findTitle} aria-label={findTitle}>
          <Medallion icon="pin" />
        </a>
        <a href="#histoires" title="Ses histoires" aria-label="Ses histoires">
          <Medallion icon="quill" />
        </a>
      </nav>

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
              <div>
                <dt>Classe</dt>
                <dd>{c.class ? CLASS_LABELS[c.class] : <em>Un mystère, pour l'instant</em>}</dd>
              </div>
              {c.level && (
                <div>
                  <dt>Niveau</dt>
                  <dd>{c.level}</dd>
                </div>
              )}
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
          </Sheet>

          {c.ooc_note && (
            <Sheet variant="muted" seed={`${c.id}-hrp`} age={age}>
              <h2 className={styles.oocTitle}>Un mot hors RP</h2>
              <p className={styles.ooc}>{c.ooc_note}</p>
            </Sheet>
          )}

          <div className={styles.report}>
            <ReportButton target="character" targetId={c.id} mine={c.is_mine ?? false} />
            <IgnoreButton character={c} />
          </div>
          <TeamBox target="character" id={c.id} />
        </aside>
      </div>

      <section id="histoires" className={styles.stories} aria-labelledby="histoires-titre">
        <div className={`paper-tag ${styles.storiesHead}`}>
          <Medallion icon="quill" />
          <h2 id="histoires-titre">Ses histoires</h2>
          {c.is_mine && <Link to="/histoires/nouvelle">Écrire une histoire</Link>}
        </div>
        <StoryList
          filters={{ characterId: c.id }}
          ofCharacter
          empty={agree(c.gender, {
            feminine: "Elle n'a encore rien raconté.",
            masculine: "Il n'a encore rien raconté.",
            neutral: "Rien de raconté pour l'instant.",
          })}
        />
      </section>
    </main>
  )
}

export default CharacterPage
