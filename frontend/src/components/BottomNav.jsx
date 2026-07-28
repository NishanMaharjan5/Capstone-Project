import { NavLink } from 'react-router-dom'

const TABS = [
  { to: '/', label: 'Home', icon: '⌂', end: true },
  { to: '/history', label: 'History', icon: '≡' },
  { to: '/add', label: 'Add', icon: '+' },
  { to: '/analytics', label: 'Analytics', icon: '◔' },
  { to: '/profile', label: 'Profile', icon: '☺' },
]

export default function BottomNav() {
  return (
    <nav className="lg:hidden fixed bottom-0 left-0 right-0 bg-surface border-t border-border px-4 py-2 flex justify-between items-center z-30">
      {TABS.map((tab) => (
        <NavLink
          key={tab.to}
          to={tab.to}
          end={tab.end}
          className={({ isActive }) =>
            `flex flex-col items-center gap-1 px-3 py-2 rounded-xl text-xs transition-colors ${
              isActive ? 'bg-mint-light text-ink font-semibold' : 'text-muted'
            }`
          }
        >
          <span className="text-base">{tab.icon}</span>
          {tab.label}
        </NavLink>
      ))}
    </nav>
  )
}
