import { Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout'
import { DashboardPage } from './pages/DashboardPage'
import { MyAccountPage } from './pages/MyAccountPage'
import { BuildOptimizerPage } from './pages/BuildOptimizerPage'
import { UpgradeAdvisorPage } from './pages/UpgradeAdvisorPage'
import { SettingsPage } from './pages/SettingsPage'

function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<DashboardPage />} />
        <Route path="account" element={<MyAccountPage />} />
        <Route path="build-optimizer" element={<BuildOptimizerPage />} />
        <Route path="upgrade-advisor" element={<UpgradeAdvisorPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>
    </Routes>
  )
}

export default App
