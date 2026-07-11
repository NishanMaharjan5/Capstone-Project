import { useState } from 'react'
import { formatMoney } from '../utils/receiptMath'

export default function MonthlyBudgetCard({ amount, allocated, unallocated, onSave }) {
  const [isEditing, setIsEditing] = useState(false)
  const [value, setValue] = useState(amount ? String(amount) : '')
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState('')

  const hasBudget = amount != null
  const progress = hasBudget && amount > 0 ? Math.min((allocated / amount) * 100, 100) : 0

  function startEditing() {
    setValue(amount ? String(amount) : '')
    setError('')
    setIsEditing(true)
  }

  async function handleSave() {
    const num = Number(value)
    if (!num || num <= 0) {
      setError('Enter an amount greater than zero.')
      return
    }
    setIsSaving(true)
    setError('')
    try {
      await onSave(num)
      setIsEditing(false)
    } catch (err) {
      setError(err.message || 'Could not save monthly budget')
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="panel">
      <h2>Monthly budget</h2>

      {!hasBudget && !isEditing ? <p>Set your monthly budget to start dividing it across categories.</p> : null}

      {hasBudget ? (
        <>
          <p className="total-spent">{formatMoney(amount)} per month</p>
          <div className="budget-progress">
            <div className="budget-progress-fill" style={{ width: `${progress}%` }} />
          </div>
          <div className="budget-row-figures">
            <span>Allocated to categories: {formatMoney(allocated)}</span>
            <span>Left to allocate: {formatMoney(unallocated)}</span>
          </div>
        </>
      ) : null}

      {isEditing ? (
        <div className="budget-row-edit">
          <input
            type="number"
            min="0"
            step="0.01"
            placeholder="Monthly budget"
            value={value}
            onChange={(e) => setValue(e.target.value)}
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
          <button type="button" className="secondary-button" onClick={startEditing}>
            {hasBudget ? 'Change monthly budget' : 'Set monthly budget'}
          </button>
        </div>
      )}

      {error ? <div className="alert error">{error}</div> : null}
    </div>
  )
}
