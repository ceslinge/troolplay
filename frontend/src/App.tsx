import { BrowserRouter, Route, Routes } from 'react-router'
import Layout from './components/Layout'
import AccountPage from './pages/AccountPage'
import CharacterPage from './pages/CharacterPage'
import CommunityPage, { CommunityIndex } from './pages/CommunityPage'
import CreateCharacterPage from './pages/CreateCharacterPage'
import ForgotPasswordPage from './pages/ForgotPasswordPage'
import HomePage from './pages/HomePage'
import LoginPage from './pages/LoginPage'
import ResetPasswordPage from './pages/ResetPasswordPage'
import SignupPage from './pages/SignupPage'
import VerifyPage from './pages/VerifyPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<HomePage />} />
          <Route path="/communaute" element={<CommunityIndex />} />
          <Route path="/communaute/:serverId" element={<CommunityPage />} />
          <Route path="/personnages/nouveau" element={<CreateCharacterPage />} />
          <Route path="/personnages/:id" element={<CharacterPage />} />
          <Route path="/connexion" element={<LoginPage />} />
          <Route path="/inscription" element={<SignupPage />} />
          <Route path="/verifier" element={<VerifyPage />} />
          <Route path="/mot-de-passe-oublie" element={<ForgotPasswordPage />} />
          <Route path="/mot-de-passe" element={<ResetPasswordPage />} />
          <Route path="/compte" element={<AccountPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
