import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { useAuth } from '../auth/AuthContext'
import { getActiveTrip } from '../api/trips'

const TripContext = createContext(null)

// Mounted app-wide (see App.jsx) so both the OCR review step and manual entry
// can check "is there an active trip" without each fetching it independently.
export function TripProvider({ children }) {
  const { isAuthenticated } = useAuth()
  const [activeTrip, setActiveTrip] = useState(null)

  const refreshActiveTrip = useCallback(async () => {
    if (!isAuthenticated) {
      setActiveTrip(null)
      return
    }
    try {
      const data = await getActiveTrip()
      setActiveTrip(data.trip)
    } catch {
      setActiveTrip(null)
    }
  }, [isAuthenticated])

  useEffect(() => {
    refreshActiveTrip()
  }, [refreshActiveTrip])

  const value = { activeTrip, refreshActiveTrip }

  return <TripContext.Provider value={value}>{children}</TripContext.Provider>
}

export function useTrip() {
  const context = useContext(TripContext)
  if (!context) {
    throw new Error('useTrip must be used inside TripProvider')
  }
  return context
}
