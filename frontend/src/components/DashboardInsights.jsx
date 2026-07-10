import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import InsightsPanel from './InsightsPanel'
import { getAnalytics } from '../api/receipts'
import { formatMoney } from '../utils/receiptMath'

const MAX_INSIGHTS = 5

export default function DashboardInsights({ refreshKey }) {
  const [insights, setInsights] = useState([])
  const [monthTotal, setMonthTotal] = useState(0)
  const [receiptCount, setReceiptCount] = useState(0)
  const [error, setError] = useState('')

  useEffect(() => {
    let ignore = false

    async function load() {
      try {
        const data = await getAnalytics()
        if (ignore || !data.success) return
        setInsights((data.analytics.insights || []).slice(0, MAX_INSIGHTS))
        setMonthTotal(data.analytics.summary?.current_month_total || 0)
        setReceiptCount(data.analytics.summary?.receipt_count || 0)
      } catch (err) {
        if (!ignore) setError(err.message || 'Could not load analytics')
      }
    }

    load()
    return () => {
      ignore = true
    }
  }, [refreshKey])

  if (error) return <div className="alert error">{error}</div>

  return (
    <div className="dashboard-insights">
      <h2>Insights</h2>

      {receiptCount === 0 ? (
        <p>Add a few receipts and your spending insights will show up here.</p>
      ) : (
        <>
          <p className="total-spent">This month so far: {formatMoney(monthTotal)}</p>
          <InsightsPanel insights={insights} expandable={false} />
          <Link to="/analytics" className="link-button">
            View full analytics →
          </Link>
        </>
      )}
    </div>
  )
}
