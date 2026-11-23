import { BrowserRouter, Route, Routes } from 'react-router'
import CharacterPage from './pages/CharacterPage'
import HomePage from './pages/HomePage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/personnages/:id" element={<CharacterPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
