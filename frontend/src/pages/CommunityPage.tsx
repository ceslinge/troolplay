import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { useEffect, useRef, useState } from 'react'
import { Link, Navigate, useNavigate, useParams, useSearchParams } from 'react-router'
import { type DirectoryFilters, fetchCharacters, PAGE_SIZE, type Period } from '../api/characters'
import { fetchPlaces, fetchServers } from '../api/servers'
import CharacterCard from '../components/CharacterCard'
import Chips from '../components/Chips'
import Medallion from '../components/Medallion'
import Menu from '../components/Menu'
import PlaceCard from '../components/PlaceCard'
import Sheet from '../components/Sheet'
import StoryList from '../components/StoryList'
import Unreachable from '../components/Unreachable'
import { useActiveCharacter, useMyCharacters } from '../lib/activeCharacter'
import { DAY_OPTIONS, PERIOD_OPTIONS } from '../lib/schedule'
import { useMe } from '../lib/useMe'
import { serverOptions } from '../lib/games'
import PageTitle from '../components/PageTitle'
import styles from './CommunityPage.module.css'
import { plural } from '../lib/text'
import Notice from '../components/Notice'
import StatusPage from '../components/StatusPage'
import buttons from '../components/Button.module.css'

/** /communaute tout court : le serveur du personnage actif, ou à défaut le premier. */
export function CommunityIndex() {
  const servers = useQuery({ queryKey: ['servers'], queryFn: fetchServers })
  const me = useMe()
  const mine = useMyCharacters()
  const active = useActiveCharacter()
  if (servers.isError || me.isError) return <Unreachable />
  // Connecté, on attend ses personnages pour ne pas ouvrir un serveur puis sauter à un autre.
  if (servers.isPending || me.isPending || (me.data && mine === undefined)) return null
  const list = servers.data ?? []
  // Un serveur fermé depuis n'est plus dans la liste : on retombe alors sur le premier.
  const target = list.find((s) => s.id === active?.server?.id) ?? list[0]
  return target ? (
    <Navigate to={`/communaute/${target.id}`} replace />
  ) : (
    <StatusPage
      tab="Aucun serveur"
      icon="compass"
      title="Aucun serveur pour l'instant"
      lead="Le panneau n'a encore aucun serveur où présenter des personnages. Repasse un peu plus tard."
    >
      <Link to="/" className={`${buttons.button} ${buttons.primary}`}>
        Retour à l'accueil
      </Link>
    </StatusPage>
  )
}

type Tab = 'lieux' | 'personnages' | 'histoires'

function CommunityPage({ tab }: { tab: Tab }) {
  const { serverId = '' } = useParams()
  const [params, setParams] = useSearchParams()
  const navigate = useNavigate()

  const servers = useQuery({ queryKey: ['servers'], queryFn: fetchServers })
  const server = servers.data?.find((s) => String(s.id) === serverId)

  // Les filtres vivent dans l'adresse : une recherche se partage par un simple lien.
  const filters: DirectoryFilters = {
    serverId: Number(serverId),
    day: Number(params.get('day')) || undefined,
    period: (params.get('period') as Period | null) ?? undefined,
    q: params.get('q')?.trim().slice(0, 60) || undefined,
    includeInactive: params.get('retrait') === 'oui',
    page: Number(params.get('page')) || 1,
  }

  const characters = useQuery({
    queryKey: ['characters', filters],
    queryFn: () => fetchCharacters(filters),
    enabled: server !== undefined && tab === 'personnages',
    placeholderData: keepPreviousData,
  })
  const places = useQuery({
    queryKey: ['places', filters.serverId, filters.day, filters.period],
    queryFn: () => fetchPlaces(filters.serverId, filters),
    enabled: server !== undefined && tab === 'lieux',
    placeholderData: keepPreviousData,
  })

  /** L'adresse d'un onglet : jour et créneau suivent, nom et retrait ne valent que pour l'annuaire. */
  function tabLink(target: Tab, id: number | string = serverId) {
    const kept = new URLSearchParams()
    const keys = { lieux: ['day', 'period'], personnages: ['day', 'period', 'q', 'retrait'], histoires: [] }[target]
    for (const key of keys) {
      const value = params.get(key)
      if (value) kept.set(key, value)
    }
    const query = kept.size ? `?${kept}` : ''
    return `/communaute/${id}${target === 'personnages' ? '' : `/${target}`}${query}`
  }

  function setFilter(key: string, value: string | undefined, options?: { replace?: boolean }) {
    // Toujours à partir de l'adresse du moment : une recherche différée ne doit pas effacer un filtre choisi entre-temps.
    setParams((current) => {
      const next = new URLSearchParams(current)
      if (value) next.set(key, value)
      else next.delete(key)
      next.delete('page')
      return next
    }, options)
  }

  // Ce qu'on tape s'affiche tout de suite, la recherche part après une courte pause.
  const [typed, setTyped] = useState(params.get('q') ?? '')
  // L'adresse peut changer sans nous (« Retour », un autre onglet) : le champ la suit alors.
  const inAddress = params.get('q') ?? ''
  const [seen, setSeen] = useState(inAddress)
  if (inAddress !== seen) {
    setSeen(inAddress)
    if (typed.trim() !== inAddress) setTyped(inAddress)
  }
  const pending = useRef<ReturnType<typeof setTimeout>>(undefined)
  useEffect(() => () => clearTimeout(pending.current), [])
  function search(text: string) {
    setTyped(text)
    clearTimeout(pending.current)
    // Chaque lettre ne crée pas une page d'historique : « Retour » ramène d'où l'on vient.
    pending.current = setTimeout(() => setFilter('q', text.trim() || undefined, { replace: true }), 300)
  }

  // Sur téléphone, les filtres se replient derrière « Affiner » ; un filtre déjà choisi les laisse ouverts.
  const active = [filters.day, filters.period, filters.q, filters.includeInactive || undefined].filter(Boolean).length
  const [refining, setRefining] = useState(active > 0)

  function goToPage(page: number) {
    const next = new URLSearchParams(params)
    next.set('page', String(page))
    setParams(next)
  }

  if (servers.isError) {
    return <Unreachable />
  }
  if (servers.isPending) {
    return null
  }
  if (!server) {
    return (
      <StatusPage
        tab="Serveur introuvable"
        icon="compass"
        title="Ce serveur n'existe pas, ou plus"
        lead="Il a peut-être fermé. Les fiches et les histoires qui y vivaient restent lisibles depuis leurs liens."
      >
        <Link to="/communaute" className={`${buttons.button} ${buttons.primary}`}>
          Voir la communauté
        </Link>
      </StatusPage>
    )
  }

  const total = characters.data?.total ?? 0
  const pages = Math.max(1, Math.ceil(total / PAGE_SIZE))

  return (
    <main className={styles.page}>
      <PageTitle>{`Communauté de ${server.name}`}</PageTitle>
      <div className={styles.top}>
        <Sheet seed={`${server.id}-titre`} contentClassName={styles.title}>
          <span className={styles.kicker}>Communauté du serveur</span>
          <Menu
            label="Changer de serveur"
            hideLabel
            variant="title"
            value={server.id}
            options={serverOptions(servers.data, (s) => s.id)}
            onChange={(id) => navigate(tabLink(tab, id))}
          />
        </Sheet>

        <nav className={styles.tabs} aria-label="Sections de la communauté">
          <Link
            to={tabLink('lieux')}
            className={`${styles.tab} ${tab === 'lieux' ? styles.current : ''}`}
            aria-current={tab === 'lieux' ? 'page' : undefined}
          >
            <Medallion icon="pin" tone={tab === 'lieux' ? 'dark' : 'light'} /> Qui traîne ici ?
          </Link>
          <Link
            to={tabLink('personnages')}
            className={`${styles.tab} ${tab === 'personnages' ? styles.current : ''}`}
            aria-current={tab === 'personnages' ? 'page' : undefined}
          >
            <Medallion icon="eye" tone={tab === 'personnages' ? 'dark' : 'light'} /> Personnages
          </Link>
          <Link
            to={tabLink('histoires')}
            className={`${styles.tab} ${tab === 'histoires' ? styles.current : ''}`}
            aria-current={tab === 'histoires' ? 'page' : undefined}
          >
            <Medallion icon="quill" tone={tab === 'histoires' ? 'dark' : 'light'} /> Histoires
          </Link>
        </nav>
      </div>

      {tab !== 'histoires' && (
        <button
          type="button"
          className={styles.refine}
          aria-expanded={refining}
          onClick={() => setRefining(!refining)}
        >
          {refining ? 'Masquer les filtres' : active > 0 ? `Affiner (${active})` : 'Affiner'}
        </button>
      )}
      {tab !== 'histoires' && (
        <Sheet edge="straight" className={refining ? undefined : styles.folded} contentClassName={styles.filters}>
          <Chips
            legend="Joue le"
            options={DAY_OPTIONS}
            value={filters.day}
            onChange={(day) => setFilter('day', day ? String(day) : undefined)}
          />
          <Chips
            legend="Plutôt"
            options={PERIOD_OPTIONS}
            value={filters.period}
            onChange={(period) => setFilter('period', period)}
          />
          {tab === 'personnages' && (
            <>
              <label className={styles.field}>
                <span>Chercher un nom</span>
                <input
                  type="search"
                  value={typed}
                  onChange={(event) => search(event.target.value)}
                  placeholder="Maëlis, ou son nom en jeu…"
                  maxLength={60}
                  autoComplete="off"
                  spellCheck={false}
                />
              </label>
              <label className={styles.check}>
                <input
                  type="checkbox"
                  checked={filters.includeInactive}
                  onChange={(event) => setFilter('retrait', event.target.checked ? 'oui' : undefined)}
                />
                Inclure ceux en retrait
              </label>
            </>
          )}
        </Sheet>
      )}

      {tab === 'histoires' ? (
        <StoryList
          filters={{ serverId: Number(serverId), page: Number(params.get('page')) || 1 }}
          onPage={goToPage}
          empty={`Aucune histoire sur ${server.name} pour l'instant. La première attend peut-être la tienne.`}
        />
      ) : tab === 'lieux' ? (
        <>
          {/* En panne, on ne compte rien : « personne » serait faux. */}
          <p className={styles.count} aria-live="polite" hidden={places.isError}>
            {places.isPending
              ? 'On parcourt le panneau…'
              : places.data?.length
                ? `${plural(places.data.length, 'lieu', 'lieux')} où traîner`
                : 'Personne n’a encore épinglé de lieu, à ce moment-là.'}
          </p>
          {places.isError && (
            <Notice tone="error">
              <p>Impossible de charger les lieux. Réessaie dans un moment.</p>
            </Notice>
          )}
          <div className={styles.places}>
            {places.data?.map((place) => (
              <PlaceCard key={`${place.area}-${place.x}-${place.y}`} place={place} />
            ))}
          </div>
        </>
      ) : (
        <>
          <p className={styles.count} aria-live="polite" hidden={characters.isError}>
            {characters.isPending
              ? 'On parcourt le panneau…'
              : total === 0
                ? 'Personne ne correspond, pour l’instant.'
                : plural(total, 'personnage')}
          </p>

          {characters.isError && (
            <Notice tone="error">
              <p>Impossible de charger les personnages. Réessaie dans un moment.</p>
            </Notice>
          )}

          <div className={styles.grid}>
            {characters.data?.items.map((character) => (
              <CharacterCard key={character.id} character={character} />
            ))}
          </div>

          {pages > 1 && (
            <nav className={styles.pagination} aria-label="Pages">
              <button type="button" disabled={filters.page <= 1} onClick={() => goToPage(filters.page - 1)}>
                Précédents
              </button>
              <span>
                Page {filters.page} sur {pages}
              </span>
              <button type="button" disabled={filters.page >= pages} onClick={() => goToPage(filters.page + 1)}>
                Suivants
              </button>
            </nav>
          )}
        </>
      )}
    </main>
  )
}

export default CommunityPage
