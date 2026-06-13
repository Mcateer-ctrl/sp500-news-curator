import { Routes, Route, Link } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Settings from './pages/Settings'
import AlertRules from './pages/AlertRules'
import NotificationBell from './components/NotificationBell'

export default function App() {
  return (
    <div className="min-h-screen">
      <nav className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
        <Link to="/" className="text-xl font-bold text-blue-700">
          S&P 500 News Curator
        </Link>
        <div className="flex items-center gap-4">
          <Link to="/" className="text-gray-600 hover:text-blue-600 font-medium">
            Dashboard
          </Link>
          <Link to="/alerts" className="text-gray-600 hover:text-blue-600 font-medium">
            Alerts
          </Link>
          <Link to="/settings" className="text-gray-600 hover:text-blue-600 font-medium">
            Settings
          </Link>
          <NotificationBell />
        </div>
      </nav>
      <main>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/alerts" element={<AlertRules />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </main>
    </div>
  )
}
