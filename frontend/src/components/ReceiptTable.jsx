import { Fragment, useState } from 'react'
import ReceiptDetail from './ReceiptDetail'
import { formatMoney } from '../utils/receiptMath'

export default function ReceiptTable({ receipts, onDelete }) {
  const [expandedId, setExpandedId] = useState(null)
  const [deleteError, setDeleteError] = useState('')

  const total = receipts.reduce((sum, r) => sum + (Number(r.total) || 0), 0)
  const latest = receipts[0]?.vendor || '—'

  async function handleDelete(id) {
    if (!window.confirm('Delete this receipt?')) return

    setDeleteError('')
    try {
      await onDelete(id)
    } catch (err) {
      setDeleteError(err.message || 'Failed to delete receipt')
    }
  }

  if (receipts.length === 0) {
    return (
      <div className="panel">
        <p>No receipts yet. Upload one or add manually!</p>
      </div>
    )
  }

  return (
    <div className="panel">
      <div className="stat-bar">
        <div className="stat-tile">
          <span className="field-label">Receipts</span>
          <strong>{receipts.length}</strong>
        </div>
        <div className="stat-tile">
          <span className="field-label">Total</span>
          <strong>{formatMoney(total)}</strong>
        </div>
        <div className="stat-tile">
          <span className="field-label">Latest</span>
          <strong>{latest}</strong>
        </div>
      </div>

      {deleteError ? <div className="alert error">{deleteError}</div> : null}

      <table className="data-table">
        <thead>
          <tr>
            <th>Vendor</th>
            <th>Date</th>
            <th>Total</th>
            <th>Source</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {receipts.map((receipt) => (
            <Fragment key={receipt._id}>
              <tr>
                <td>{receipt.vendor || 'Unknown vendor'}</td>
                <td>{receipt.date || receipt.created_at?.split('T')[0] || '—'}</td>
                <td>{formatMoney(receipt.total)}</td>
                <td>
                  <span className={`source-badge${receipt.source === 'manual' ? ' manual' : ''}`}>
                    {receipt.source === 'manual' ? '✏️ Manual' : '📷 OCR'}
                  </span>
                </td>
                <td className="actions-cell">
                  <button
                    type="button"
                    className="link-button"
                    onClick={() => setExpandedId(expandedId === receipt._id ? null : receipt._id)}
                  >
                    {expandedId === receipt._id ? 'Hide Details' : 'View Details'}
                  </button>
                  <button type="button" className="link-button danger" onClick={() => handleDelete(receipt._id)}>
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
    </div>
  )
}
