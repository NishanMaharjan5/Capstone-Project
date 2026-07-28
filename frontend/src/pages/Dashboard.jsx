import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { getBudgetOverview } from '../api/budgets'
import { getIncome } from '../api/income'
import DashboardInsights from '../components/DashboardInsights'
import RecentReceipts from '../components/RecentReceipts'
import { useUpload } from '../receipts/UploadContext'
import { formatMoney } from '../utils/receiptMath'

function getGreeting() {
  const hour = new Date().getHours()
  if (hour < 12) return 'Good morning'
  if (hour < 18) return 'Good afternoon'
  return 'Good evening'
}

function StatCard({ label, value, tone = 'default' }) {
  const toneClass = {
    default: 'bg-surface',
    mint: 'bg-mint-light',
    lav: 'bg-lav-light',
    rose: 'bg-rose-light',
  }[tone]

  return (
    <div className={`${toneClass} rounded-xl2 shadow-soft p-5 flex flex-col gap-1`}>
      <span className="field-label">{label}</span>
      <span className="text-2xl font-bold text-ink">{value}</span>
    </div>
  )
}

export default function Dashboard() {
  const { user } = useAuth()
  const { refreshKey } = useUpload()
  const firstName = (user?.name || 'there').split(' ')[0]

  const [monthSpent, setMonthSpent] = useState(0)
  const [totalIncome, setTotalIncome] = useState(0)
  const [monthlyBudget, setMonthlyBudget] = useState(null)

  useEffect(() => {
    let ignore = false

    async function loadStats() {
      try {
        const [budgetData, incomeData] = await Promise.all([getBudgetOverview(), getIncome()])
        if (ignore) return
        const summary = budgetData.budget_overview?.summary || {}
        setMonthSpent(summary.total_spent || 0)
        setMonthlyBudget(summary.total_monthly_budget || null)
        setTotalIncome(incomeData.total || 0)
      } catch {
        // Stat cards are supplementary — DashboardInsights already surfaces
        // load errors for the analytics data itself, so fail quietly here.
      }
    }

    loadStats()
    return () => {
      ignore = true
    }
  }, [refreshKey])

  const netBalance = totalIncome - monthSpent
  const budgetUsedLabel = monthlyBudget
    ? `${Math.min(100, Math.round((monthSpent / monthlyBudget) * 100))}%`
    : '—'

  return (
    <section className="page-view">
      <div className="section-heading">
        <p className="eyebrow">Dashboard</p>
        <h1>
          {getGreeting()}, {firstName}
        </h1>
        <p>Here's how your spending is looking.</p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Net Balance" value={formatMoney(netBalance)} tone="mint" />
        <StatCard label="Total Income" value={formatMoney(totalIncome)} tone="lav" />
        <StatCard label="Total Spent" value={formatMoney(monthSpent)} tone="rose" />
        <StatCard label="Budget Used" value={budgetUsedLabel} />
      </div>

      <div className="flex flex-wrap gap-3">
        <Link to="/add" className="secondary-button">+ Add expense</Link>
        <Link to="/scan" className="secondary-button">Scan a receipt</Link>
        <Link to="/income" className="secondary-button">Log income</Link>
      </div>

      <DashboardInsights refreshKey={refreshKey} />

      <RecentReceipts refreshKey={refreshKey} />
    </section>
  )
}
