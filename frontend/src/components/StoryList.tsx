import { keepPreviousData, useInfiniteQuery, useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { fetchStories, STORIES_PAGE_SIZE, type StoryFilters, type StoryOrder, type StorySummary } from '../api/stories'
import { useMe } from '../lib/useMe'
import MembersOnly from './MembersOnly'
import Menu from './Menu'
import StoryCard from './StoryCard'
import styles from './StoryList.module.css'

type Group = { key: number; stories: StorySummary[] }

/** Personne n'occupe tout le panneau : les histoires qui se suivent d'un même personnage
 * se rangent sous la première (décision 28). */
function groupByCharacter(stories: StorySummary[]): Group[] {
  const groups: Group[] = []
  for (const story of stories) {
    const last = groups.at(-1)
    if (last && last.stories[0].character?.id === story.character?.id) last.stories.push(story)
    else groups.push({ key: story.id, stories: [story] })
  }
  return groups
}

function StoryGroup({ group }: { group: Group }) {
  const [open, setOpen] = useState(false)
  const [first, ...more] = group.stories
  const name = first.character?.name
  return (
    <div className={styles.group}>
      <StoryCard story={first} />
      {more.length > 0 &&
        (open ? (
          more.map((story) => <StoryCard key={story.id} story={story} />)
        ) : (
          <button type="button" className={styles.more} onClick={() => setOpen(true)}>
            Et {more.length} autre{more.length > 1 ? 's' : ''} histoire{more.length > 1 ? 's' : ''} de {name}
          </button>
        ))}
    </div>
  )
}

type Props = {
  filters: StoryFilters
  /** Sur la fiche d'un personnage : pas de regroupement, et pas besoin de le nommer. */
  ofCharacter?: boolean
  onPage?: (page: number) => void
  /** Ce qu'on dit quand la liste est vide. */
  empty: string
}

/** Les histoires d'un serveur, page par page, regroupées par personnage. */
function ServerStories({ filters, onPage, empty }: Props) {
  const me = useMe()
  const stories = useQuery({
    queryKey: ['stories', filters],
    queryFn: () => fetchStories(filters),
    enabled: Boolean(me.data),
    placeholderData: keepPreviousData,
  })

  if (me.isPending) return null
  if (!me.data) return <MembersOnly />
  if (stories.isError) return <p className={styles.count}>Impossible de charger les histoires. Réessaie dans un moment.</p>

  const total = stories.data?.total ?? 0
  const page = filters.page ?? 1
  const pages = Math.max(1, Math.ceil(total / STORIES_PAGE_SIZE))

  return (
    <>
      <p className={styles.count} aria-live="polite">
        {stories.isPending ? 'On parcourt le panneau…' : total === 0 ? empty : `${total} histoire${total > 1 ? 's' : ''}`}
      </p>
      <div className={styles.list}>
        {groupByCharacter(stories.data?.items ?? []).map((group) => (
          <StoryGroup key={group.key} group={group} />
        ))}
      </div>
      {pages > 1 && onPage && (
        <nav className={styles.pagination} aria-label="Pages">
          <button type="button" disabled={page <= 1} onClick={() => onPage(page - 1)}>
            Plus récentes
          </button>
          <span>
            Page {page} sur {pages}
          </span>
          <button type="button" disabled={page >= pages} onClick={() => onPage(page + 1)}>
            Plus anciennes
          </button>
        </nav>
      )}
    </>
  )
}

// Sur une fiche : quelques histoires d'abord, la fiche ne doit pas devenir un mur ; la suite à la demande.
const FIRST = 5
const MORE = 10

/** Les histoires d'un personnage, sur sa fiche : les plus récentes, puis « Voir plus » jusqu'au bout. */
function CharacterStories({ filters, empty }: Props) {
  const me = useMe()
  const [order, setOrder] = useState<StoryOrder>('newest')
  const stories = useInfiniteQuery({
    queryKey: ['stories', 'character', filters.characterId, order],
    // pageParam : combien d'histoires sont déjà affichées. Les premières, puis un paquet de plus à chaque clic.
    queryFn: ({ pageParam }) => fetchStories({ ...filters, order }, pageParam === 0 ? FIRST : MORE, pageParam),
    initialPageParam: 0,
    getNextPageParam: (last, all) => {
      const shown = all.reduce((n, page) => n + page.items.length, 0)
      return shown < last.total ? shown : undefined
    },
    enabled: Boolean(me.data),
  })

  if (me.isPending) return null
  if (!me.data) return <MembersOnly />
  if (stories.isError) return <p className={styles.count}>Impossible de charger les histoires. Réessaie dans un moment.</p>

  const items = stories.data?.pages.flatMap((page) => page.items) ?? []
  const total = stories.data?.pages[0]?.total ?? 0

  return (
    <>
      <div className={styles.bar}>
        <p className={styles.count} aria-live="polite">
          {stories.isPending ? 'On parcourt le panneau…' : total === 0 ? empty : `${total} histoire${total > 1 ? 's' : ''}`}
        </p>
        {total > 1 && (
          <Menu<StoryOrder>
            label="Ordre des histoires"
            hideLabel
            variant="compact"
            value={order}
            options={[
              { value: 'newest', label: "Les plus récentes d'abord" },
              { value: 'oldest', label: 'Depuis le début' },
            ]}
            onChange={setOrder}
          />
        )}
      </div>
      <div className={styles.list}>
        {items.map((story) => (
          <StoryCard key={story.id} story={story} showCharacter={false} />
        ))}
      </div>
      {stories.hasNextPage && (
        <button
          type="button"
          className={styles.more}
          disabled={stories.isFetchingNextPage}
          onClick={() => void stories.fetchNextPage()}
        >
          {stories.isFetchingNextPage
            ? 'Un instant…'
            : Math.min(MORE, total - items.length) === 1
              ? 'Voir la suivante'
              : `Voir les ${Math.min(MORE, total - items.length)} suivantes`}
        </button>
      )}
    </>
  )
}

/** Les histoires publiées d'un serveur ou d'un personnage, pour les membres seulement. */
function StoryList(props: Props) {
  return props.ofCharacter ? <CharacterStories {...props} /> : <ServerStories {...props} />
}

export default StoryList
