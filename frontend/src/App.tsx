import { Routes, Route, Link, useLocation } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Settings from './pages/Settings'
import AlertRules from './pages/AlertRules'
import NotificationBell from './components/NotificationBell'

function NavLink({ to, label }: { to: string; label: string }) {
  const location = useLocation()
  const active = location.pathname === to
  return (
    <Link
      to={to}
      className={`relative px-4 py-1.5 text-sm font-medium rounded-full transition-colors duration-200 ${
        active
          ? 'text-accent bg-accent-light'
          : 'text-stone-500 hover:text-stone-800'
      }`}
    >
      {label}
    </Link>
  )
}

export default function App() {
  return (
    <div className="min-h-[100dvh] bg-surface">
      {/* Grain texture overlay */}
      <div className="grain-overlay" aria-hidden="true" />

      {/* Floating nav pill */}
      <nav className="fixed top-4 left-1/2 -translate-x-1/2 z-50">
        <div className="bg-white/80 backdrop-blur-xl ring-1 ring-black/[0.06] shadow-pill rounded-full px-2 py-1.5 flex items-center gap-1">
          <Link to="/" className="text-sm font-semibold text-stone-800 px-3 mr-1 tracking-tight">
            S&P 500 Curator
          </Link>
          <div className="w-px h-5 bg-black/10 mx-1" />
          <NavLink to="/" label="Dashboard" />
          <NavLink to="/alerts" label="Alerts" />
          <NavLink to="/settings" label="Settings" />
          <div className="w-px h-5 bg-black/10 mx-1" />
          <NotificationBell />
        </div>
      </nav>

      {/* Main content */}
      <main className="pt-20 pb-8">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/alerts" element={<AlertRules />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </main>
    </div>
  )
}