import { Suspense, lazy } from 'react'
import { BrowserRouter, Link, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider, useAuth } from './auth/AuthContext'
import ProtectedRoute from './auth/ProtectedRoute'
import UserMenu from './components/UserMenu'
import Dashboard from './pages/Dashboard'
import ForgotPassword from './pages/ForgotPassword'
import History from './pages/History'
import Login from './pages/Login'
import Register from './pages/Register'
import { UploadProvider, useUpload } from './receipts/UploadContext'

// Lazy-loaded: pulls in Plotly, which is large — no reason to ship it on every route.
const Analytics = lazy(() => import('./pages/Analytics'))
const Budgets = lazy(() => import('./pages/Budgets'))

function AppLayout({ children }) {
  const { isAuthenticated, logout, user } = useAuth()
  const { isAnalyzing, draft } = useUpload()

  return (
    <div className="app-shell">
      <header className="topbar">
        <Link to="/" className="brand">
          Receipt Analyzer
        </Link>
        <nav className="nav-links" aria-label="Main navigation">
          {isAuthenticated ? (
            <>
              <Link to="/">Dashboard</Link>
              <Link to="/history">History</Link>
              <Link to="/analytics">Analytics</Link>
              <Link to="/budgets">Budgets</Link>
              {isAnalyzing ? (
                <span className="user-chip">Analyzing receipt...</span>
              ) : draft ? (
                <Link to="/" className="user-chip">
                  Receipt ready to review
                </Link>
              ) : null}
              <UserMenu user={user} onLogout={logout} />
            </>
          ) : (
            <>
              <Link to="/login">Login</Link>
              <Link to="/register">Register</Link>
            </>
          )}
        </nav>
      </header>
      <main>{children}</main>
    </div>
  )
}

function AppRoutes() {
  return (
    <AppLayout>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route element={<ProtectedRoute />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/history" element={<History />} />
          <Route
            path="/analytics"
            element={
              <Suspense fallback={<p>Loading analytics...</p>}>
                <Analytics />
              </Suspense>
            }
          />
          <Route
            path="/budgets"
            element={
              <Suspense fallback={<p>Loading budgets...</p>}>
                <Budgets />
              </Suspense>
            }
          />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppLayout>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <UploadProvider>
          <AppRoutes />
        </UploadProvider>
      </AuthProvider>
    </BrowserRouter>
  )
}
