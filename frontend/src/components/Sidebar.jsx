import { NavLink } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

const NAV = [
  { to: '/', label: 'Dashboard', icon: '⌂', end: true },
  { to: '/add', label: 'Add Expense', icon: '+' },
  { to: '/scan', label: 'Scan Receipt', icon: '▤' },
  { to: '/history', label: 'History', icon: '≡' },
  { to: '/budgets', label: 'Budgets', icon: '◎' },
  { to: '/trips', label: 'Trips', icon: '✈' },
  { to: '/income', label: 'Income', icon: '↑' },
  { to: '/analytics', label: 'Analytics', icon: '◔' },
]

export default function Sidebar() {
  const { user, logout } = useAuth()
  const name = user?.name

  return (
    <aside className="hidden lg:flex w-64 flex-col bg-surface border-r border-border h-screen sticky top-0 px-5 py-8">
      <div className="flex items-center gap-2 px-2">
        <div className="w-8 h-8 rounded-lg bg-mint-dark" />
        <span className="text-lg font-bold text-ink">Centa</span>
      </div>

      <nav className="mt-10 flex-1 space-y-1 overflow-y-auto no-scrollbar">
        {NAV.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
          >
            <span className="nav-icon">{item.icon}</span>
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-border pt-4 mt-4">
        <NavLink to="/profile" className={({ isActive }) => `nav-item mb-1 ${isActive ? 'active' : ''}`}>
          <span className="w-8 h-8 rounded-full bg-sand flex items-center justify-center font-semibold text-ink text-xs flex-shrink-0">
            {name ? name[0].toUpperCase() : '?'}
          </span>
          {name || 'Profile'}
        </NavLink>
        <button onClick={logout} className="nav-item text-rose-dark hover:bg-rose-light">
          <span className="nav-icon">⏻</span>
          Log out
        </button>
      </div>
    </aside>
  )
}
