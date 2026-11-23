import { useEffect, useState } from 'react'
import { Link } from 'react-router'

type Health = 'loading' | 'ok' | 'down'

function HomePage() {
  const [health, setHealth] = useState<Health>('loading')

  useEffect(() => {
    fetch('/api/health')
      .then((response) => setHealth(response.ok ? 'ok' : 'down'))
      .catch(() => setHealth('down'))
  }, [])

  return (
    <main>
      <h1>TroolPlay</h1>
      {health === 'loading' && <p>On frappe à la porte du backend…</p>}
      {health === 'ok' && <p>Le backend répond, le panneau est prêt.</p>}
      {health === 'down' && <p>Le backend ne répond pas. Il tourne bien ?</p>}
      <p>
        <Link to="/communaute">Voir la communauté</Link>
      </p>
    </main>
  )
}

export default HomePage