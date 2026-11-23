import { BrowserRouter, Route, Routes } from 'react-router'
import CharacterPage from './pages/CharacterPage'
import CommunityPage, { CommunityIndex } from './pages/CommunityPage'
import HomePage from './pages/HomePage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/communaute" element={<CommunityIndex />} />
        <Route path="/communaute/:serverId" element={<CommunityPage />} />
        <Route path="/personnages/:id" element={<CharacterPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
