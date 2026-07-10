import { useEffect, useState } from 'react'
import AnalyticsTabs from '../components/analytics/AnalyticsTabs'
import CategoryBreakdownChart from '../components/CategoryBreakdownChart'
import CategoryComparisonChart from '../components/CategoryComparisonChart'
import DayOfWeekChart from '../components/DayOfWeekChart'
import InsightsPanel from '../components/InsightsPanel'
import PaceProjectionChart from '../components/PaceProjectionChart'
import SpendingTrendChart from '../components/SpendingTrendChart'
import SummaryStats from '../components/SummaryStats'
import TopVendorsList from '../components/TopVendorsList'
import { getAnalytics } from '../api/receipts'

export default function Analytics() {
  const [analytics, setAnalytics] = useState(null)
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('overview')

  useEffect(() => {
    let ignore = false

    async function load() {
      setIsLoading(true)
      setError('')

      try {
        const data = await getAnalytics()
        if (!ignore) setAnalytics(data.analytics)
      } catch (err) {
        if (!ignore) setError(err.message || 'Could not load analytics')
      } finally {
        if (!ignore) setIsLoading(false)
      }
    }

    load()
    return () => {
      ignore = true
    }
  }, [])

  return (
    <section className="page-view">
      <div className="section-heading">
        <p className="eyebrow">Insights</p>
        <h1>Spending analytics</h1>
        <p>How your spending breaks down by category, over time, and by vendor.</p>
      </div>

      {error ? <div className="alert error">{error}</div> : null}

      {isLoading ? (
        <p>Loading analytics...</p>
      ) : analytics && analytics.summary.receipt_count > 0 ? (
        <>
          <div className="panel">
            <h2>Insights</h2>
            <InsightsPanel insights={analytics.insights} figures={analytics.figures} />
          </div>

          <AnalyticsTabs active={activeTab} onChange={setActiveTab} />

          {activeTab === 'overview' ? (
            <div className="panel">
              <SummaryStats summary={analytics.summary} />
            </div>
          ) : null}

          {activeTab === 'time' ? (
            <>
              <div className="panel">
                <h2>This month's pace</h2>
                <PaceProjectionChart figure={analytics.figures.pace_projection} />
              </div>

              <div className="panel">
                <h2>Spending over time</h2>
                <SpendingTrendChart figure={analytics.figures.monthly_trend} />
              </div>

              <div className="panel">
                <h2>Spending by day of week</h2>
                <DayOfWeekChart figure={analytics.figures.day_of_week} />
              </div>
            </>
          ) : null}

          {activeTab === 'category' ? (
            <>
              <div className="panel">
                <h2>Spending by category</h2>
                <CategoryBreakdownChart figure={analytics.figures.category} />
              </div>

              <div className="panel">
                <h2>This month vs last month, by category</h2>
                <CategoryComparisonChart figure={analytics.figures.category_comparison} />
              </div>
            </>
          ) : null}

          {activeTab === 'vendor' ? (
            <div className="panel">
              <h2>Top vendors</h2>
              <TopVendorsList vendors={analytics.top_vendors} />
            </div>
          ) : null}
        </>
      ) : (
        <div className="panel">
          <p>No receipts yet — upload one or add a manual entry to see your spending analytics.</p>
        </div>
      )}
    </section>
  )
}
