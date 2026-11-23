import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import '@fontsource-variable/bitter'
import '@fontsource-variable/work-sans'
import './index.css'
import App from './App.tsx'
import Toaster from './components/Toaster'

const queryClient = new QueryClient()

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <Toaster>
        <App />
      </Toaster>
    </QueryClientProvider>
  </StrictMode>,
)
