import { useEffect, useState } from 'react'
import BudgetCategoryRow from '../components/BudgetCategoryRow'
import BudgetComparisonChart from '../components/BudgetComparisonChart'
import DecisionSupportBubble from '../components/DecisionSupportBubble'
import { clearBudget, getBudgetOverview, setBudget } from '../api/budgets'
import { formatMoney } from '../utils/receiptMath'

export default function Budgets() {
  const [overview, setOverview] = useState(null)
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(true)

  async function load() {
    setError('')
    try {
      const data = await getBudgetOverview()
      setOverview(data.budget_overview)
    } catch (err) {
      setError(err.message || 'Could not load budgets')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  async function handleSave(category, amount) {
    await setBudget(category, amount)
    await load()
  }

  async function handleClear(category) {
    await clearBudget(category)
    await load()
  }

  return (
    <section className="page-view">
      <div className="section-heading">
        <p className="eyebrow">Budgets</p>
        <h1>Budget management</h1>
        <p>Set a monthly budget per category and track how this month's spending measures up.</p>
      </div>

      {error ? <div className="alert error">{error}</div> : null}

      {isLoading ? (
        <p>Loading budgets...</p>
      ) : overview ? (
        <>
          <div className="panel">
            <div className="stat-bar">
              <div className="stat-tile">
                <span className="field-label">Total monthly budget</span>
                <strong>{formatMoney(overview.summary.total_budgeted)}</strong>
              </div>
              <div className="stat-tile">
                <span className="field-label">Spent against budget</span>
                <strong>{formatMoney(overview.summary.total_spent)}</strong>
              </div>
              <div className="stat-tile">
                <span className="field-label">Needs attention</span>
                <strong>
                  {overview.summary.over_count} over · {overview.summary.warning_count} near limit
                </strong>
              </div>
            </div>
          </div>

          <div className="panel">
            <h2>Budget vs actual, by category</h2>
            <BudgetComparisonChart figure={overview.figure} />
          </div>

          <div className="panel">
            <h2>Categories</h2>
            <div className="budget-row-list">
              {overview.categories.map((row) => (
                <BudgetCategoryRow key={row.category} row={row} onSave={handleSave} onClear={handleClear} />
              ))}
            </div>
          </div>
        </>
      ) : null}

      <DecisionSupportBubble />
    </section>
  )
}
