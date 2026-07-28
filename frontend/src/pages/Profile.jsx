import { useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

export default function Profile() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  return (
    <section className="page-view">
      <div className="section-heading">
        <p className="eyebrow">Profile</p>
        <h1>Your account</h1>
      </div>

      <div className="panel max-w-md">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 rounded-full bg-sand flex items-center justify-center font-bold text-ink text-xl flex-shrink-0">
            {user?.name ? user.name[0].toUpperCase() : '?'}
          </div>
          <div>
            <div className="font-bold text-ink text-lg">{user?.name || 'User'}</div>
            <div className="text-muted text-sm">{user?.email}</div>
          </div>
        </div>

        <div className="border-t border-border pt-4 mt-2 flex flex-col gap-1">
          <button type="button" className="nav-item justify-between" onClick={() => navigate('/budgets')}>
            Budget settings <span className="text-muted">→</span>
          </button>
          <button type="button" className="nav-item justify-between" onClick={() => navigate('/income')}>
            Income sources <span className="text-muted">→</span>
          </button>
          <button type="button" className="nav-item justify-between" onClick={() => navigate('/trips')}>
            Trips <span className="text-muted">→</span>
          </button>
        </div>

        <button
          type="button"
          onClick={logout}
          className="w-full mt-2 border border-rose text-rose-dark font-semibold py-3 rounded-xl hover:bg-rose-light"
        >
          Log out
        </button>
      </div>
    </section>
  )
}
