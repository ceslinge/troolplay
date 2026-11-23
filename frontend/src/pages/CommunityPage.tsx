import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { Navigate, useNavigate, useParams, useSearchParams } from 'react-router'
import {
  type CharacterClass,
  type DirectoryFilters,
  fetchCharacters,
  PAGE_SIZE,
  type Period,
} from '../api/characters'
import { fetchServers } from '../api/servers'
import CharacterCard from '../components/CharacterCard'
import Chips from '../components/Chips'
import Medallion from '../components/Medallion'
import Sheet from '../components/Sheet'
import { CLASS_LABELS } from '../lib/classes'
import { DAY_OPTIONS, PERIOD_OPTIONS } from '../lib/schedule'
import styles from './CommunityPage.module.css'

/** /communaute tout court : on ouvre le premier serveur. */
export function CommunityIndex() {
  const servers = useQuery({ queryKey: ['servers'], queryFn: fetchServers })
  if (servers.isPending) return null
  const first = servers.data?.[0]
  return first ? <Navigate to={`/communaute/${first.id}`} replace /> : <p>Aucun serveur pour l'instant.</p>
}

function CommunityPage() {
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
    characterClass: (params.get('class') as CharacterClass | null) ?? undefined,
    includeInactive: params.get('retrait') === 'oui',
    page: Number(params.get('page')) || 1,
  }

  const characters = useQuery({
    queryKey: ['characters', filters],
    queryFn: () => fetchCharacters(filters),
    enabled: server !== undefined,
    placeholderData: keepPreviousData,
  })

  function setFilter(key: string, value: string | undefined) {
    const next = new URLSearchParams(params)
    if (value) next.set(key, value)
    else next.delete(key)
    next.delete('page')
    setParams(next)
  }

  function goToPage(page: number) {
    const next = new URLSearchParams(params)
    next.set('page', String(page))
    setParams(next)
  }

  if (servers.isError) {
    return <p className={styles.page}>Le panneau est inaccessible pour l'instant.</p>
  }
  if (servers.isPending) {
    return null
  }
  if (!server) {
    return <p className={styles.page}>Ce serveur n'existe pas, ou plus.</p>
  }

  const total = characters.data?.total ?? 0
  const pages = Math.max(1, Math.ceil(total / PAGE_SIZE))

  return (
    <main className={styles.page}>
      <div className={styles.top}>
        <Sheet seed={`${server.id}-titre`} contentClassName={styles.title}>
          <span className={styles.kicker}>Communauté du serveur</span>
          <label className={styles.serverPicker}>
            <span className={styles.visuallyHidden}>Changer de serveur</span>
            <select
              value={server.id}
              onChange={(event) => navigate(`/communaute/${event.target.value}`)}
            >
              {servers.data.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </label>
        </Sheet>

        <nav className={styles.tabs} aria-label="Sections de la communauté">
          <span className={styles.tab} aria-disabled="true" title="Bientôt">
            <Medallion icon="pin" /> Qui traîne ici ?
          </span>
          <span className={`${styles.tab} ${styles.current}`} aria-current="page">
            <Medallion icon="eye" tone="dark" /> Personnages
          </span>
          <span className={styles.tab} aria-disabled="true" title="Bientôt">
            <Medallion icon="quill" /> Histoires
          </span>
        </nav>
      </div>

      <Sheet edge="straight" contentClassName={styles.filters}>
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
        <label className={styles.field}>
          <span>Classe</span>
          <select
            value={filters.characterClass ?? ''}
            onChange={(event) => setFilter('class', event.target.value || undefined)}
          >
            <option value="">Toutes</option>
            {server.classes.map((c) => (
              <option key={c} value={c}>
                {CLASS_LABELS[c]}
              </option>
            ))}
          </select>
        </label>
        <label className={styles.check}>
          <input
            type="checkbox"
            checked={filters.includeInactive}
            onChange={(event) => setFilter('retrait', event.target.checked ? 'oui' : undefined)}
          />
          Inclure ceux en retrait
        </label>
      </Sheet>

      <p className={styles.count} aria-live="polite">
        {characters.isPending
          ? 'On parcourt le panneau…'
          : total === 0
            ? 'Personne ne correspond, pour l’instant.'
            : `${total} personnage${total > 1 ? 's' : ''}`}
      </p>

      {characters.isError && <p>Impossible de charger les personnages. Réessaie dans un moment.</p>}

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
    </main>
  )
}

export default CommunityPage
