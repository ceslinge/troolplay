import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import '@fontsource-variable/bitter'
import '@fontsource-variable/work-sans'
import './index.css'
import { ApiError } from './api/client'
import App from './App.tsx'
import Toaster from './components/Toaster'

// Une seule nouvelle tentative, et seulement si le serveur a flanché : un refus (4xx) ne changera pas.
// Par défaut il y en a trois, et la page reste vide plusieurs secondes avant d'afficher l'erreur.
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: (failures, error) => failures < 1 && !(error instanceof ApiError && error.status >= 400 && error.status < 500),
    },
  },
})

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <Toaster>
        <App />
      </Toaster>
    </QueryClientProvider>
  </StrictMode>,
)
