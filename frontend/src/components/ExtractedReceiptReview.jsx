import { useState } from 'react'
import { CATEGORIES } from '../constants/categories'
import { computeLineTotal, formatMoney } from '../utils/receiptMath'

export default function ExtractedReceiptReview({ draft, onSave, onDiscard, isSaving, saveError }) {
  const [category, setCategory] = useState('')
  const [showRaw, setShowRaw] = useState(false)
  const [categoryError, setCategoryError] = useState('')

  const extracted = draft.extracted_data || {}
  const items = Array.isArray(extracted.items) ? extracted.items : []

  function handleSave() {
    if (!category) {
      setCategoryError('Please select a category before saving.')
      return
    }
    setCategoryError('')
    onSave(category)
  }

  return (
    <div className="panel">
      <h2>Extracted receipt</h2>

      <div className="review-grid">
        <div>
          <span className="field-label">Vendor</span>
          <p>{extracted.vendor || '—'}</p>
        </div>
        <div>
          <span className="field-label">Date</span>
          <p>{extracted.date || '—'}</p>
        </div>
        <div>
          <span className="field-label">Total</span>
          <p>{formatMoney(extracted.total)}</p>
        </div>
        <div>
          <span className="field-label">Status</span>
          <span className={`badge ${extracted.verified ? 'verified' : 'unverified'}`}>
            {extracted.verified ? '✓ Verified' : '✗ Unverified'}
          </span>
        </div>
      </div>

      <label>
        Category
        <select
          value={category}
          onChange={(e) => {
            setCategory(e.target.value)
            setCategoryError('')
          }}
        >
          <option value="" disabled>
            Select category
          </option>
          {CATEGORIES.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
      </label>
      {categoryError ? <div className="alert error">{categoryError}</div> : null}

      {items.length > 0 ? (
        <table className="data-table">
          <thead>
            <tr>
              <th>Item</th>
              <th>Total</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item, index) => (
              <tr key={index}>
                <td>
                  {(item.name || 'Unknown item')} x{Number(item.quantity) || 1}
                </td>
                <td>{formatMoney(computeLineTotal(item))}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : null}

      <div className="raw-toggle">
        <button type="button" className="link-button" onClick={() => setShowRaw((v) => !v)}>
          {showRaw ? '▼' : '▶'} Show raw JSON
        </button>
        {showRaw ? <pre className="raw-json">{JSON.stringify(draft, null, 2)}</pre> : null}
      </div>

      {saveError ? <div className="alert error">{saveError}</div> : null}

      <div className="button-row">
        <button type="button" className="primary-button" onClick={handleSave} disabled={isSaving}>
          {isSaving ? 'Saving...' : 'Save Receipt'}
        </button>
        <button type="button" className="secondary-button" onClick={onDiscard} disabled={isSaving}>
          Discard Draft
        </button>
      </div>
    </div>
  )
}
