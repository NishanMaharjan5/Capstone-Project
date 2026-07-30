import { Fragment, useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import ReceiptDetail from '../components/ReceiptDetail'
import TripCategoryChart from '../components/TripCategoryChart'
import TripCumulativeChart from '../components/TripCumulativeChart'
import TripDayBreakdown from '../components/TripDayBreakdown'
import TripVendorsChart from '../components/TripVendorsChart'
import { deleteTrip, endTrip, getTripDetail } from '../api/trips'
import { deleteReceipt } from '../api/receipts'
import { useTrip } from '../trips/TripContext'
import { formatMoney } from '../utils/receiptMath'

export default function TripDetail() {
  const { tripId } = useParams()
  const navigate = useNavigate()
  const { refreshActiveTrip } = useTrip()
  const [trip, setTrip] = useState(null)
  const [summary, setSummary] = useState(null)
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [isEnding, setIsEnding] = useState(false)
  const [expandedId, setExpandedId] = useState(null)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [deletePassword, setDeletePassword] = useState('')
  const [deleteError, setDeleteError] = useState('')
  const [isDeleting, setIsDeleting] = useState(false)

  async function load() {
    setIsLoading(true)
    setError('')
    try {
      const data = await getTripDetail(tripId)
      setTrip(data.trip)
      setSummary(data.summary)
    } catch (err) {
      setError(err.message || 'Could not load trip')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tripId])

  async function handleEnd() {
    if (!window.confirm('End this trip? No more receipts can be added to it afterward.')) return

    setIsEnding(true)
    try {
      await endTrip(tripId)
      await refreshActiveTrip()
      await load()
    } catch (err) {
      setError(err.message || 'Could not end trip')
    } finally {
      setIsEnding(false)
    }
  }

  async function handleDeleteReceipt(id) {
    if (!window.confirm('Delete this receipt?')) return

    try {
      await deleteReceipt(id)
      await load()
    } catch (err) {
      setError(err.message || 'Could not delete receipt')
    }
  }

  async function handleDelete() {
    if (!deletePassword) {
      setDeleteError('Please enter your password to confirm.')
      return
    }
    setDeleteError('')
    setIsDeleting(true)
    try {
      await deleteTrip(tripId, deletePassword)
      navigate('/trips')
    } catch (err) {
      setDeleteError(err.message || 'Could not delete trip')
    } finally {
      setIsDeleting(false)
    }
  }

  if (isLoading) {
    return (
      <section className="page-view">
        <p>Loading trip...</p>
      </section>
    )
  }

  if (error || !trip) {
    return (
      <section className="page-view">
        <div className="alert error">{error || 'Trip not found'}</div>
      </section>
    )
  }

  return (
    <section className="page-view">
      <div className="section-heading">
        <p className="eyebrow">Trips</p>
        <h1>{trip.name}</h1>
        <p>
          {trip.destination ? `${trip.destination} · ` : ''}
          {trip.start_date}
          {trip.ended_at ? ` – ${trip.ended_at.slice(0, 10)}` : ' (in progress)'}
        </p>
      </div>

      {trip.status === 'active' ? (
        <div className="button-row">
          <button type="button" className="secondary-button" onClick={handleEnd} disabled={isEnding}>
            {isEnding ? 'Ending...' : 'End trip'}
          </button>
        </div>
      ) : null}

      <div className="panel">
        <div className="stat-bar">
          <div className="stat-tile">
            <span className="field-label">Total spent</span>
            <strong>{formatMoney(summary.stats.total_spent)}</strong>
          </div>
          <div className="stat-tile">
            <span className="field-label">Receipts</span>
            <strong>{summary.stats.receipt_count}</strong>
          </div>
          <div className="stat-tile">
            <span className="field-label">Days</span>
            <strong>{summary.stats.day_count}</strong>
          </div>
          <div className="stat-tile">
            <span className="field-label">Avg per day</span>
            <strong>{formatMoney(summary.stats.avg_daily_spend)}</strong>
          </div>
        </div>
      </div>

      {summary.total_budget || summary.budget_progress.length > 0 ? (
        <div className="panel">
          <h2>Budget vs actual</h2>
          {summary.total_budget ? (
            <p className="recent-meta">
              Trip budget: {formatMoney(summary.total_budget)} · Allocated: {formatMoney(summary.allocated_budget)} ·
              Left to allocate: {formatMoney(summary.total_budget - summary.allocated_budget)}
            </p>
          ) : null}
          <div className="budget-row-list">
            {summary.budget_progress.map((row) => {
              const pct = row.limit ? Math.min((row.spent / row.limit) * 100, 100) : 0
              return (
                <div className="budget-row" key={row.category}>
                  <div className="budget-row-header">
                    <strong>{row.category}</strong>
                    <span className={`status-pill ${row.status}`}>
                      {formatMoney(row.spent)} / {formatMoney(row.limit)}
                    </span>
                  </div>
                  <div className="budget-progress">
                    <div className={`budget-progress-fill ${row.status}`} style={{ width: `${pct}%` }} />
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      ) : null}

      <div className="panel">
        <h2>Spending over the trip</h2>
        <TripCumulativeChart figure={summary.figures.cumulative_spend} />
      </div>

      <div className="panel">
        <h2>Spending by day</h2>
        <TripDayBreakdown figure={summary.figures.by_day} receipts={summary.receipts} />
      </div>

      <div className="panel">
        <h2>Spending by category</h2>
        <TripCategoryChart figure={summary.figures.by_category} />
      </div>

      <div className="panel">
        <h2>Top vendors</h2>
        <TripVendorsChart figure={summary.figures.top_vendors} />
      </div>

      <div className="panel">
        <h2>Receipts</h2>
        {summary.receipts.length === 0 ? (
          <p>No receipts tagged to this trip yet.</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Vendor</th>
                <th>Date</th>
                <th>Category</th>
                <th>Total</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {summary.receipts.map((receipt) => (
                <Fragment key={receipt._id}>
                  <tr>
                    <td>{receipt.vendor || 'Unknown vendor'}</td>
                    <td>{receipt.date}</td>
                    <td>{receipt.category}</td>
                    <td>{formatMoney(receipt.total)}</td>
                    <td className="actions-cell">
                      <button
                        type="button"
                        className="link-button"
                        onClick={() => setExpandedId(expandedId === receipt._id ? null : receipt._id)}
                      >
                        {expandedId === receipt._id ? 'Hide Details' : 'View Details'}
                      </button>
                      <button type="button" className="link-button danger" onClick={() => handleDeleteReceipt(receipt._id)}>
                        Delete
                      </button>
                    </td>
                  </tr>
                  {expandedId === receipt._id ? (
                    <tr>
                      <td colSpan={5}>
                        <ReceiptDetail receipt={receipt} />
                      </td>
                    </tr>
                  ) : null}
                </Fragment>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {trip.status === 'ended' ? (
        <div className="panel">
          <h2>Delete trip</h2>
          <p className="recent-meta">
            This removes the trip and its tracking, not your receipts — any receipts tagged to it go back to being
            regular history entries.
          </p>

          {showDeleteConfirm ? (
            <div className="manual-form">
              <label>
                Confirm your password
                <input
                  type="password"
                  value={deletePassword}
                  onChange={(e) => {
                    setDeletePassword(e.target.value)
                    setDeleteError('')
                  }}
                />
              </label>
              {deleteError ? <div className="alert error">{deleteError}</div> : null}
              <div className="button-row">
                <button type="button" className="link-button danger" onClick={handleDelete} disabled={isDeleting}>
                  {isDeleting ? 'Deleting...' : 'Confirm delete'}
                </button>
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => {
                    setShowDeleteConfirm(false)
                    setDeletePassword('')
                    setDeleteError('')
                  }}
                  disabled={isDeleting}
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <button type="button" className="link-button danger" onClick={() => setShowDeleteConfirm(true)}>
              Delete this trip
            </button>
          )}
        </div>
      ) : null}
    </section>
  )
}
