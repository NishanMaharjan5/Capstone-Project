import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { TRIP_CATEGORIES } from '../constants/tripCategories'
import { createTrip, endTrip, getTripDetail, listTrips } from '../api/trips'
import { useTrip } from '../trips/TripContext'
import { formatMoney } from '../utils/receiptMath'

function emptyBudgets() {
  return Object.fromEntries(TRIP_CATEGORIES.map((c) => [c, '']))
}

export default function Trips() {
  const { activeTrip, refreshActiveTrip } = useTrip()
  const [trips, setTrips] = useState([])
  const [activeSummary, setActiveSummary] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [isEnding, setIsEnding] = useState(false)

  const [name, setName] = useState('')
  const [destination, setDestination] = useState('')
  const [startDate, setStartDate] = useState('')
  const [plannedEndDate, setPlannedEndDate] = useState('')
  const [wantsBudget, setWantsBudget] = useState(false)
  const [totalBudget, setTotalBudget] = useState('')
  const [budgets, setBudgets] = useState(emptyBudgets)
  const [formError, setFormError] = useState('')
  const [isCreating, setIsCreating] = useState(false)

  const totalBudgetAmount = Number(totalBudget) || 0
  const allocatedAmount = Object.values(budgets).reduce((sum, v) => sum + (Number(v) || 0), 0)
  const remainingAmount = totalBudgetAmount - allocatedAmount

  async function load() {
    setIsLoading(true)
    setError('')
    try {
      const data = await listTrips()
      setTrips(data.trips || [])
      if (activeTrip) {
        const detail = await getTripDetail(activeTrip._id)
        setActiveSummary(detail.summary)
      } else {
        setActiveSummary(null)
      }
    } catch (err) {
      setError(err.message || 'Could not load trips')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTrip])

  async function handleCreate() {
    if (!name.trim()) {
      setFormError('Please enter a trip name.')
      return
    }
    if (!startDate) {
      setFormError('Please choose a start date.')
      return
    }
    if (wantsBudget && totalBudgetAmount <= 0) {
      setFormError('Enter a trip budget greater than zero.')
      return
    }
    setFormError('')
    setIsCreating(true)

    try {
      const budgetPayload = wantsBudget
        ? Object.fromEntries(
            Object.entries(budgets)
              .filter(([, v]) => v && Number(v) > 0)
              .map(([k, v]) => [k, Number(v)]),
          )
        : {}
      await createTrip({
        name: name.trim(),
        destination: destination.trim() || null,
        start_date: startDate,
        planned_end_date: plannedEndDate || null,
        total_budget: wantsBudget ? totalBudgetAmount : null,
        budgets: budgetPayload,
      })
      setName('')
      setDestination('')
      setStartDate('')
      setPlannedEndDate('')
      setWantsBudget(false)
      setTotalBudget('')
      setBudgets(emptyBudgets())
      await refreshActiveTrip()
    } catch (err) {
      setFormError(err.message || 'Could not create trip')
    } finally {
      setIsCreating(false)
    }
  }

  async function handleEnd() {
    if (!activeTrip) return
    if (!window.confirm('End this trip? No more receipts can be added to it afterward.')) return

    setIsEnding(true)
    try {
      await endTrip(activeTrip._id)
      await refreshActiveTrip()
    } catch (err) {
      setError(err.message || 'Could not end trip')
    } finally {
      setIsEnding(false)
    }
  }

  const pastTrips = trips.filter((t) => t.status === 'ended')

  return (
    <section className="page-view">
      <div className="section-heading">
        <p className="eyebrow">Trips</p>
        <h1>Trip tracker</h1>
        <p>Track spending on a trip from start to finish, then keep the full summary forever.</p>
      </div>

      {error ? <div className="alert error">{error}</div> : null}

      {activeTrip ? (
        <div className="panel">
          <div className="trip-active-header">
            <div>
              <h2>{activeTrip.name}</h2>
              <p className="recent-meta">
                {activeTrip.destination ? `${activeTrip.destination} · ` : ''}Started {activeTrip.start_date}
              </p>
            </div>
            <span className="status-pill ok">Active</span>
          </div>

          {activeSummary && (activeSummary.total_budget || activeSummary.budget_progress.length > 0) ? (
            <div className="budget-row-list">
              {activeSummary.total_budget ? (
                <p className="recent-meta">
                  Trip budget: {formatMoney(activeSummary.total_budget)} · Allocated: {formatMoney(activeSummary.allocated_budget)} ·
                  Left to allocate: {formatMoney(activeSummary.total_budget - activeSummary.allocated_budget)}
                </p>
              ) : null}
              {activeSummary.budget_progress.map((row) => {
                const pct = row.limit ? Math.min((row.spent / row.limit) * 100, 100) : 0
                return (
                  <div className="budget-row" key={row.category}>
                    <div className="budget-row-header">
                      <strong>{row.category}</strong>
                      <span>{formatMoney(row.spent)} / {formatMoney(row.limit)}</span>
                    </div>
                    <div className="budget-progress">
                      <div className={`budget-progress-fill ${row.status}`} style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                )
              })}
            </div>
          ) : null}

          <div className="button-row">
            <Link to={`/trips/${activeTrip._id}`} className="primary-button">
              View trip
            </Link>
            <button type="button" className="secondary-button" onClick={handleEnd} disabled={isEnding}>
              {isEnding ? 'Ending...' : 'End trip'}
            </button>
          </div>
        </div>
      ) : (
        <div className="panel">
          <h2>Start a new trip</h2>
          <div className="manual-form">
            <label>
              Trip name
              <input type="text" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Pokhara Trip" />
            </label>
            <label>
              Destination
              <input type="text" value={destination} onChange={(e) => setDestination(e.target.value)} placeholder="Optional" />
            </label>
            <label>
              Start date
              <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
            </label>
            <label>
              Planned end date
              <input type="date" value={plannedEndDate} onChange={(e) => setPlannedEndDate(e.target.value)} />
            </label>

            <label className="trip-tag-toggle">
              <input
                type="checkbox"
                checked={wantsBudget}
                onChange={(e) => {
                  setWantsBudget(e.target.checked)
                  if (!e.target.checked) {
                    setTotalBudget('')
                    setBudgets(emptyBudgets())
                  }
                }}
              />
              Set a budget for this trip?
            </label>

            {wantsBudget ? (
              <div>
                <label>
                  Total trip budget
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    placeholder="Rs."
                    value={totalBudget}
                    onChange={(e) => setTotalBudget(e.target.value)}
                  />
                </label>

                {totalBudgetAmount > 0 ? (
                  <div>
                    <span className="field-label">Divide it across categories (optional)</span>
                    <div className="trip-budget-grid">
                      {TRIP_CATEGORIES.map((c) => (
                        <label key={c}>
                          {c}
                          <input
                            type="number"
                            min="0"
                            step="0.01"
                            placeholder="Rs."
                            value={budgets[c]}
                            onChange={(e) => setBudgets((prev) => ({ ...prev, [c]: e.target.value }))}
                          />
                        </label>
                      ))}
                    </div>
                    <p className="recent-meta">
                      {remainingAmount < 0
                        ? `Rs. ${(-remainingAmount).toFixed(2)} over your trip budget — lower a category to fit.`
                        : `Rs. ${remainingAmount.toFixed(2)} left to allocate`}
                    </p>
                  </div>
                ) : (
                  <p className="recent-meta">Enter a trip budget above to start dividing it across categories.</p>
                )}
              </div>
            ) : null}

            {formError ? <div className="alert error">{formError}</div> : null}

            <div className="button-row">
              <button type="button" className="primary-button" onClick={handleCreate} disabled={isCreating}>
                {isCreating ? 'Creating...' : 'Start trip'}
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="panel">
        <h2>Past trips</h2>
        {isLoading ? (
          <p>Loading trips...</p>
        ) : pastTrips.length === 0 ? (
          <p>No past trips yet.</p>
        ) : (
          <div className="trip-card-grid">
            {pastTrips.map((trip) => (
              <div className="trip-card" key={trip._id}>
                <h3>{trip.name}</h3>
                <p className="recent-meta">
                  {trip.destination ? `${trip.destination} · ` : ''}
                  {trip.start_date}
                  {trip.ended_at ? ` – ${trip.ended_at.slice(0, 10)}` : ''}
                </p>
                <p className="total-spent">{formatMoney(trip.total_spent)}</p>
                <Link to={`/trips/${trip._id}`} className="secondary-button">
                  View summary
                </Link>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  )
}
