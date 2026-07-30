import { Suspense, lazy } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider, useAuth } from './auth/AuthContext'
import ProtectedRoute from './auth/ProtectedRoute'
import AppShell from './components/AppShell'
import AddExpense from './pages/AddExpense'
import Dashboard from './pages/Dashboard'
import ForgotPassword from './pages/ForgotPassword'
import History from './pages/History'
import Login from './pages/Login'
import Profile from './pages/Profile'
import Register from './pages/Register'
import ScanReceipt from './pages/ScanReceipt'
import { UploadProvider } from './receipts/UploadContext'
import { TripProvider } from './trips/TripContext'

// Lazy-loaded: pulls in Plotly, which is large — no reason to ship it on every route.
const Analytics = lazy(() => import('./pages/Analytics'))
const Budgets = lazy(() => import('./pages/Budgets'))
const Income = lazy(() => import('./pages/Income'))
const Trips = lazy(() => import('./pages/Trips'))
const TripDetail = lazy(() => import('./pages/TripDetail'))

function AppLayout({ children }) {
  const { isAuthenticated } = useAuth()

  if (!isAuthenticated) {
    return <main className="min-h-screen bg-cream">{children}</main>
  }

  return <AppShell>{children}</AppShell>
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
          <Route path="/add" element={<AddExpense />} />
          <Route path="/scan" element={<ScanReceipt />} />
          <Route path="/history" element={<History />} />
          <Route path="/profile" element={<Profile />} />
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
          <Route
            path="/income"
            element={
              <Suspense fallback={<p>Loading income...</p>}>
                <Income />
              </Suspense>
            }
          />
          <Route
            path="/trips"
            element={
              <Suspense fallback={<p>Loading trips...</p>}>
                <Trips />
              </Suspense>
            }
          />
          <Route
            path="/trips/:tripId"
            element={
              <Suspense fallback={<p>Loading trip...</p>}>
                <TripDetail />
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
          <TripProvider>
            <AppRoutes />
          </TripProvider>
        </UploadProvider>
      </AuthProvider>
    </BrowserRouter>
  )
}
