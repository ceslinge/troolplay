import { useEffect, useState } from 'react'

type Health = 'loading' | 'ok' | 'down'

function App() {
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
    </main>
  )
}

export default App