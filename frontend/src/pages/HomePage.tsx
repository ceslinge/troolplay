import { useMutation, useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { Link } from 'react-router'
import type { Period } from '../api/characters'
import { fetchHome, fetchOverheard, type Overheard, type RightNow } from '../api/home'
import { fetchServers } from '../api/servers'
import CharacterCard from '../components/CharacterCard'
import Medallion from '../components/Medallion'
import Menu from '../components/Menu'
import Sheet from '../components/Sheet'
import styles from './HomePage.module.css'

const DAY_NAMES = ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche']

/** « Ce jeudi soir »… La nuit est à cheval sur deux jours : « Cette nuit, de jeudi à vendredi ». */
function moment(day: number, period: Period): string {
  const name = DAY_NAMES[day - 1]
  const before = DAY_NAMES[(day + 5) % 7]
  const forms: Record<Period, string> = {
    morning: `Ce ${name} matin`,
    afternoon: `Ce ${name} après-midi`,
    evening: `Ce ${name} soir`,
    night: `Cette nuit, de ${before} à ${name}`,
  }
  return forms[period]
}

// Le serveur choisi est retenu sur l'appareil, d'une visite à l'autre.
const SERVER_KEY = 'troolplay:serveur-accueil'

function savedServer(): number | undefined {
  try {
    return Number(localStorage.getItem(SERVER_KEY)) || undefined
  } catch {
    return undefined
  }
}

function RightNowSheet({ data, onServer }: { data: RightNow; onServer: (id: number) => void }) {
  const servers = useQuery({ queryKey: ['servers'], queryFn: fetchServers })
  const who =
    data.count === 0
      ? `personne n'a encore indiqué jouer à cette heure-ci sur ${data.server.name}.`
      : `${data.count} personnage${data.count > 1 ? 's ont' : ' a'} l'habitude d'être sur ${data.server.name}.`

  return (
    <Sheet seed="accueil-maintenant" as="section" contentClassName={styles.card}>
      <div className={styles.cardHead}>
        <Medallion icon="pin" tone="dark" />
        <h2 className={styles.cardTitle}>À cette heure-ci</h2>
        {servers.data && servers.data.length > 1 && (
          <Menu
            label="Serveur"
            hideLabel
            variant="compact"
            value={data.server.id}
            options={servers.data.map((s) => ({ value: s.id, label: s.name }))}
            onChange={onServer}
          />
        )}
      </div>
      <p className={styles.big}>
        {moment(data.day, data.period)}, {who}
      </p>
      {data.places.length > 0 && <p>Où les trouver : {data.places.join(', ')}.</p>}
      {data.count > 0 && (
        <Link to={`/communaute/${data.server.id}?day=${data.day}&period=${data.period}`}>Voir qui</Link>
      )}
      <p className={styles.note}>D'après les horaires indiqués sur les fiches : ce n'est pas qui est connecté.</p>
    </Sheet>
  )
}

function OverheardSheet({ first }: { first: Overheard }) {
  const [quote, setQuote] = useState(first)
  const another = useMutation({ mutationFn: fetchOverheard, onSuccess: (next) => next && setQuote(next) })

  return (
    <Sheet seed="accueil-comptoir" as="section" contentClassName={styles.card}>
      <div className={styles.cardHead}>
        <Medallion icon="bubbles" tone="dark" />
        <h2 className={styles.cardTitle}>Entendu au comptoir</h2>
      </div>
      <blockquote className={styles.quote}>« {quote.hook} »</blockquote>
      <p className={styles.by}>
        <Link to={`/personnages/${quote.character_id}`}>{quote.name}</Link>
        {quote.server && `, ${quote.server}`}
      </p>
      <button type="button" className={styles.again} onClick={() => another.mutate()} disabled={another.isPending}>
        Tendre l'oreille encore
      </button>
    </Sheet>
  )
}

function HomePage() {
  const [serverId, setServerId] = useState(savedServer)
  // Gardé quelques minutes : sinon la réplique du comptoir changerait à chaque retour sur l'onglet.
  const home = useQuery({ queryKey: ['home', serverId], queryFn: () => fetchHome(serverId), staleTime: 5 * 60_000 })

  function chooseServer(id: number) {
    setServerId(id)
    try {
      localStorage.setItem(SERVER_KEY, String(id))
    } catch {
      // Sans stockage, le choix vaut pour cette visite seulement.
    }
  }

  return (
    <main className={styles.page}>
      <Sheet seed="accueil" as="section" contentClassName={styles.hero}>
        <h1 className={styles.title}>Le panneau où les rôlistes de Dofus épinglent leurs personnages</h1>
        <p className={styles.lead}>
          Lis leurs fiches, repère où ils ont leurs habitudes, puis va les croiser en jeu. La suite s'écrit ici.
        </p>
        <div className={styles.actions}>
          <Link to="/communaute" className={styles.primary}>
            Découvrir la communauté
          </Link>
          <Link to="/personnages/nouveau" className={styles.secondary}>
            Présenter un nouveau personnage
          </Link>
        </div>
      </Sheet>

      {home.isError && <p className={styles.note}>Le panneau est inaccessible pour l'instant.</p>}

      {home.data && (
        <>
          <div className={styles.pair}>
            {home.data.right_now && <RightNowSheet data={home.data.right_now} onServer={chooseServer} />}
            {home.data.overheard && <OverheardSheet first={home.data.overheard} />}
          </div>

          {home.data.recent.length > 0 && (
            <section className={styles.recent} aria-labelledby="recents">
              <h2 id="recents" className={styles.band}>
                Fraîchement épinglés
              </h2>
              <div className={styles.grid}>
                {home.data.recent.map((character) => (
                  <CharacterCard key={character.id} character={character} />
                ))}
              </div>
            </section>
          )}
        </>
      )}
    </main>
  )
}

export default HomePage
