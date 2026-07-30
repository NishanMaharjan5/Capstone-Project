import { useState } from 'react'
import { CATEGORIES } from '../constants/categories'
import { TRIP_CATEGORIES } from '../constants/tripCategories'
import { addManualReceipt } from '../api/receipts'
import { useTrip } from '../trips/TripContext'
import { formatMoney } from '../utils/receiptMath'

function emptyRow() {
  return { name: '', quantity: '1', unitPrice: '' }
}

function getValidItems(rows) {
  return rows
    .map((row) => ({
      name: row.name.trim(),
      quantity: Number(row.quantity) || 0,
      unit_price: Number(row.unitPrice) || 0,
    }))
    .filter((item) => item.name && item.quantity > 0)
}

export default function ManualReceiptForm({ onSaved, defaultOpen = false }) {
  const { activeTrip } = useTrip()
  const [isOpen, setIsOpen] = useState(defaultOpen)
  const [vendor, setVendor] = useState('')
  const [date, setDate] = useState('')
  const [category, setCategory] = useState('')
  const [rows, setRows] = useState([emptyRow()])
  const [status, setStatus] = useState(null)
  const [isSaving, setIsSaving] = useState(false)
  const [addToTrip, setAddToTrip] = useState(false)

  const validItems = getValidItems(rows)
  const total = validItems.reduce((sum, item) => sum + item.quantity * item.unit_price, 0)
  const categoryOptions = activeTrip && addToTrip ? TRIP_CATEGORIES : CATEGORIES

  function updateRow(index, field, value) {
    setRows((prev) => prev.map((row, i) => (i === index ? { ...row, [field]: value } : row)))
  }

  function removeRow(index) {
    setRows((prev) => prev.filter((_, i) => i !== index))
  }

  function clearForm() {
    setVendor('')
    setDate('')
    setCategory('')
    setRows([emptyRow()])
    setAddToTrip(false)
  }

  function toggleOpen() {
    setIsOpen((prev) => {
      const next = !prev
      if (next && rows.length === 0) setRows([emptyRow()])
      return next
    })
  }

  async function handleSubmit() {
    if (!vendor.trim()) {
      setStatus({ type: 'error', message: 'Please enter the vendor name.' })
      return
    }
    if (!date) {
      setStatus({ type: 'error', message: 'Please choose the receipt date.' })
      return
    }
    if (!category) {
      setStatus({ type: 'error', message: 'Please select a category.' })
      return
    }
    if (validItems.length === 0 || !total) {
      setStatus({ type: 'error', message: 'Please add at least one item with quantity and unit price.' })
      return
    }

    setIsSaving(true)
    setStatus(null)

    try {
      await addManualReceipt({
        vendor: vendor.trim(),
        date,
        total,
        category,
        items: validItems,
        trip_id: activeTrip && addToTrip ? activeTrip._id : null,
      })
      clearForm()
      setStatus({ type: 'success', message: '✓ Receipt saved!' })
      await onSaved()
    } catch (err) {
      setStatus({ type: 'error', message: err.message || 'Failed to save receipt' })
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="panel">
      <button type="button" className="secondary-button" onClick={toggleOpen}>
        {isOpen ? '✕ Close Form' : '+ Add Manual Entry'}
      </button>

      {isOpen ? (
        <div className="manual-form">
          <label>
            Vendor
            <input type="text" value={vendor} onChange={(e) => setVendor(e.target.value)} />
          </label>
          <label>
            Date
            <input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
          </label>

          {activeTrip ? (
            <label className="trip-tag-toggle">
              <input
                type="checkbox"
                checked={addToTrip}
                onChange={(e) => {
                  setAddToTrip(e.target.checked)
                  setCategory('')
                }}
              />
              Add to {activeTrip.name}?
            </label>
          ) : null}

          <label>
            Category
            <select value={category} onChange={(e) => setCategory(e.target.value)}>
              <option value="" disabled>
                Select category
              </option>
              {categoryOptions.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </label>

          <div className="manual-items">
            {rows.map((row, index) => (
              <div className="manual-item-row" key={index}>
                <input
                  type="text"
                  placeholder="Item name"
                  value={row.name}
                  onChange={(e) => updateRow(index, 'name', e.target.value)}
                />
                <input
                  type="number"
                  min="0"
                  step="1"
                  placeholder="Qty"
                  value={row.quantity}
                  onChange={(e) => updateRow(index, 'quantity', e.target.value)}
                />
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  placeholder="Unit price"
                  value={row.unitPrice}
                  onChange={(e) => updateRow(index, 'unitPrice', e.target.value)}
                />
                <button type="button" className="link-button danger" onClick={() => removeRow(index)}>
                  ×
                </button>
              </div>
            ))}
          </div>

          <button type="button" className="link-button" onClick={() => setRows((prev) => [...prev, emptyRow()])}>
            + Add Item
          </button>

          <label>
            Total
            <input type="text" readOnly value={total ? formatMoney(total) : ''} />
          </label>

          {status ? <div className={`alert ${status.type}`}>{status.message}</div> : null}

          <div className="button-row">
            <button type="button" className="primary-button" onClick={handleSubmit} disabled={isSaving}>
              {isSaving ? 'Saving...' : 'Save Receipt'}
            </button>
            <button type="button" className="secondary-button" onClick={() => setIsOpen(false)} disabled={isSaving}>
              Discard
            </button>
          </div>
        </div>
      ) : null}
    </div>
  )
}
