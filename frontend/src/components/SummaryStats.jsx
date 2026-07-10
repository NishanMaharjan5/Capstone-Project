import { formatMoney } from '../utils/receiptMath'

export default function SummaryStats({ summary }) {
  return (
    <div className="stat-bar">
      <div className="stat-tile">
        <span className="field-label">Total spent</span>
        <strong>{formatMoney(summary.total_spent)}</strong>
      </div>
      <div className="stat-tile">
        <span className="field-label">This month</span>
        <strong>{formatMoney(summary.current_month_total)}</strong>
      </div>
      <div className="stat-tile">
        <span className="field-label">Receipts</span>
        <strong>{summary.receipt_count}</strong>
      </div>
      <div className="stat-tile">
        <span className="field-label">Avg receipt</span>
        <strong>{formatMoney(summary.average_receipt)}</strong>
      </div>
      <div className="stat-tile">
        <span className="field-label">Top category</span>
        <strong>{summary.top_category || '—'}</strong>
      </div>
    </div>
  )
}
