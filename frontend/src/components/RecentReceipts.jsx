import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getReceipts } from '../api/receipts'
import { formatMoney } from '../utils/receiptMath'

export default function RecentReceipts({ refreshKey }) {
  const [receipts, setReceipts] = useState([])
  const [totalSpent, setTotalSpent] = useState(0)
  const [error, setError] = useState('')

  useEffect(() => {
    let ignore = false

    async function load() {
      try {
        const data = await getReceipts()
        if (ignore || !data.success) return
        const all = data.receipts || []
        setReceipts(all.slice(0, 3))
        setTotalSpent(all.reduce((sum, r) => sum + (Number(r.total) || 0), 0))
      } catch (err) {
        if (!ignore) setError(err.message || 'Could not load receipts')
      }
    }

    load()
    return () => {
      ignore = true
    }
  }, [refreshKey])

  if (error) return <div className="alert error">{error}</div>

  return (
    <div className="panel">
      <h2>Recent receipts</h2>
      {receipts.length === 0 ? (
        <p>No receipts yet.</p>
      ) : (
        <>
          <p className="total-spent">Total spent: {formatMoney(totalSpent)}</p>
          <div className="recent-list">
            {receipts.map((r) => (
              <div className="recent-card" key={r._id}>
                <div>
                  <strong>{r.vendor || 'Unknown vendor'}</strong>
                  <p className="recent-meta">
                    {r.date || 'No date'} · {r.source === 'manual' ? '✏️ Manual' : '📷 OCR'}
                  </p>
                </div>
                <span>{formatMoney(r.total)}</span>
              </div>
            ))}
          </div>
        </>
      )}
      <Link to="/history" className="link-button">
        View history →
      </Link>
    </div>
  )
}
