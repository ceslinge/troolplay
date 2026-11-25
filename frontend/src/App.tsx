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
import StoryPage from './pages/StoryPage'
import WriteStoryPage from './pages/WriteStoryPage'
import { LEGAL_PAGES, type LegalPageName } from './lib/legal'

// Lues rarement : chargées à part, avec leur outil de mise en page.
const LegalPage = lazy(() => import('./pages/LegalPage'))
// L'Espace équipe ne sert qu'à quelques personnes : chargé à part, lui aussi.
const TeamHomePage = lazy(() => import('./pages/team/TeamHomePage'))
const CasesPage = lazy(() => import('./pages/team/CasesPage'))
const CasePage = lazy(() => import('./pages/team/CasePage'))
const TeamAccountPage = lazy(() => import('./pages/team/TeamAccountPage'))
const JournalPage = lazy(() => import('./pages/team/JournalPage'))
const RolesPage = lazy(() => import('./pages/team/RolesPage'))
const ServersPage = lazy(() => import('./pages/team/ServersPage'))
const ContestsPage = lazy(() => import('./pages/team/ContestsPage'))
const RequestsPage = lazy(() => import('./pages/team/RequestsPage'))

const TEAM_ROUTES = [
  { path: '/equipe', element: <TeamHomePage /> },
  { path: '/equipe/signalements', element: <CasesPage /> },
  { path: '/equipe/signalements/:kind/:id', element: <CasePage /> },
  { path: '/equipe/comptes/:id', element: <TeamAccountPage /> },
  { path: '/equipe/journal', element: <JournalPage /> },
  { path: '/equipe/roles', element: <RolesPage /> },
  { path: '/equipe/serveurs', element: <ServersPage /> },
  { path: '/equipe/contestations', element: <ContestsPage /> },
  { path: '/equipe/demandes', element: <RequestsPage /> },
]

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
          <Route path="/communaute/:serverId/histoires" element={<CommunityPage tab="histoires" />} />
          <Route path="/histoires/nouvelle" element={<WriteStoryPage />} />
          <Route path="/histoires/:id" element={<StoryPage />} />
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
          {TEAM_ROUTES.map(({ path, element }) => (
            <Route key={path} path={path} element={<Suspense>{element}</Suspense>} />
          ))}
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
