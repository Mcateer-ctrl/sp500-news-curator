import { Routes, Route, Link } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Settings from './pages/Settings'

export default function App() {
  return (
    <div className="min-h-screen">
      <nav className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
        <Link to="/" className="text-xl font-bold text-blue-700">
          S&P 500 News Curator
        </Link>
        <div className="flex gap-4">
          <Link to="/" className="text-gray-600 hover:text-blue-600 font-medium">
            Dashboard
          </Link>
          <Link to="/settings" className="text-gray-600 hover:text-blue-600 font-medium">
            Settings
          </Link>
        </div>
      </nav>
      <main>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </main>
    </div>
  )
}
