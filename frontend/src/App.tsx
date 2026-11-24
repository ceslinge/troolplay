import { lazy, Suspense } from 'react'
import { BrowserRouter, Route, Routes } from 'react-router'
import Layout from './components/Layout'
import AccountPage from './pages/AccountPage'
import CharacterPage from './pages/CharacterPage'
import CommunityPage, { CommunityIndex } from './pages/CommunityPage'
import CreateCharacterPage from './pages/CreateCharacterPage'
import EditCharacterPage from './pages/EditCharacterPage'
import ForgotPasswordPage from './pages/ForgotPasswordPage'
import HomePage from './pages/HomePage'
import LoginPage from './pages/LoginPage'
import NotFoundPage from './pages/NotFoundPage'
import ResetPasswordPage from './pages/ResetPasswordPage'
import SignupPage from './pages/SignupPage'
import VerifyPage from './pages/VerifyPage'
import WriteStoryPage from './pages/WriteStoryPage'
import { LEGAL_PAGES, type LegalPageName } from './lib/legal'

// Lues rarement : chargées à part, avec leur outil de mise en page.
const LegalPage = lazy(() => import('./pages/LegalPage'))

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<HomePage />} />
          <Route path="/communaute" element={<CommunityIndex />} />
          <Route path="/communaute/:serverId" element={<CommunityPage tab="personnages" />} />
          <Route path="/communaute/:serverId/lieux" element={<CommunityPage tab="lieux" />} />
          <Route path="/personnages/nouveau" element={<CreateCharacterPage />} />
          <Route path="/personnages/:id" element={<CharacterPage />} />
          <Route path="/personnages/:id/modifier" element={<EditCharacterPage />} />
          <Route path="/histoires/nouvelle" element={<WriteStoryPage />} />
          <Route path="/histoires/:id/modifier" element={<WriteStoryPage />} />
          <Route path="/connexion" element={<LoginPage />} />
          <Route path="/inscription" element={<SignupPage />} />
          <Route path="/verifier" element={<VerifyPage />} />
          <Route path="/mot-de-passe-oublie" element={<ForgotPasswordPage />} />
          <Route path="/mot-de-passe" element={<ResetPasswordPage />} />
          <Route path="/compte" element={<AccountPage />} />
          {(Object.keys(LEGAL_PAGES) as LegalPageName[]).map((name) => (
            <Route
              key={name}
              path={LEGAL_PAGES[name].path}
              element={
                <Suspense>
                  <LegalPage name={name} />
                </Suspense>
              }
            />
          ))}
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
