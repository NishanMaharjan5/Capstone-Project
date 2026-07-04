import { computeLineTotal, formatMoney } from '../utils/receiptMath'

export default function ReceiptDetail({ receipt }) {
  const items = Array.isArray(receipt.items) ? receipt.items : []
  const sourceLabel = receipt.source === 'manual' ? 'Manual' : 'OCR'

  return (
    <div className="receipt-paper">
      <h3>{receipt.vendor || 'Unknown vendor'}</h3>
      <p className="receipt-meta">
        {receipt.date || receipt.created_at?.split('T')[0] || '—'} · {sourceLabel}
      </p>
      <span className="category-pill">{receipt.category || 'Other'}</span>

      <table className="data-table">
        <thead>
          <tr>
            <th>Item</th>
            <th>Qty</th>
            <th>Price</th>
            <th>Total</th>
          </tr>
        </thead>
        <tbody>
          {items.length > 0 ? (
            items.map((item, index) => (
              <tr key={index}>
                <td>{item.name || 'Unknown item'}</td>
                <td>{Number(item.quantity) || 1}</td>
                <td>{formatMoney(item.unit_price ?? item.price ?? 0)}</td>
                <td>{formatMoney(computeLineTotal(item))}</td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan={4}>No items recorded</td>
            </tr>
          )}
        </tbody>
      </table>

      <p className="receipt-grand-total">Total: {formatMoney(receipt.total)}</p>
      <p className="receipt-footer">Digital receipt generated from {sourceLabel} entry</p>
    </div>
  )
}
