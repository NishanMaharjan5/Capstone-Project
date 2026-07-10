import { useState } from 'react'
import { formatMoney } from '../utils/receiptMath'

const STATUS_LABEL = {
  ok: 'On track',
  warning: 'Near limit',
  over: 'Over budget',
  no_budget: 'No budget set',
}

export default function BudgetCategoryRow({ row, onSave, onClear }) {
  const [isEditing, setIsEditing] = useState(false)
  const [amount, setAmount] = useState(row.limit ? String(row.limit) : '')
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState('')

  const hasBudget = row.limit != null
  const progress = hasBudget ? Math.min(row.pct_used, 100) : 0

  async function handleSave() {
    const value = Number(amount)
    if (!value || value <= 0) {
      setError('Enter an amount greater than zero.')
      return
    }
    setIsSaving(true)
    setError('')
    try {
      await onSave(row.category, value)
      setIsEditing(false)
    } catch (err) {
      setError(err.message || 'Could not save budget')
    } finally {
      setIsSaving(false)
    }
  }

  async function handleClear() {
    setIsSaving(true)
    try {
      await onClear(row.category)
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="budget-row">
      <div className="budget-row-header">
        <strong>{row.category}</strong>
        <span className={`status-pill ${row.status}`}>{STATUS_LABEL[row.status]}</span>
      </div>

      <div className="budget-progress">
        <div className={`budget-progress-fill ${row.status}`} style={{ width: `${progress}%` }} />
      </div>

      <div className="budget-row-figures">
        <span>Spent: {formatMoney(row.spent)}</span>
        <span>{hasBudget ? `Budget: ${formatMoney(row.limit)}` : 'No budget set'}</span>
        <span>{hasBudget ? `Remaining: ${formatMoney(row.remaining)}` : ''}</span>
      </div>

      {isEditing ? (
        <div className="budget-row-edit">
          <input
            type="number"
            min="0"
            step="0.01"
            placeholder="Monthly limit"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
          />
          <button type="button" className="primary-button" onClick={handleSave} disabled={isSaving}>
            {isSaving ? 'Saving...' : 'Save'}
          </button>
          <button type="button" className="secondary-button" onClick={() => setIsEditing(false)} disabled={isSaving}>
            Cancel
          </button>
        </div>
      ) : (
        <div className="budget-row-edit">
          <button type="button" className="secondary-button" onClick={() => setIsEditing(true)}>
            {hasBudget ? 'Change budget' : 'Set budget'}
          </button>
          {hasBudget ? (
            <button type="button" className="link-button danger" onClick={handleClear} disabled={isSaving}>
              Clear
            </button>
          ) : null}
        </div>
      )}

      {error ? <div className="alert error">{error}</div> : null}
    </div>
  )
}
