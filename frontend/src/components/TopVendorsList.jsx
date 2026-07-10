import { formatMoney } from '../utils/receiptMath'

export default function TopVendorsList({ vendors }) {
  if (!vendors || vendors.length === 0) {
    return <p>No vendors yet.</p>
  }

  return (
    <table className="data-table">
      <thead>
        <tr>
          <th>Vendor</th>
          <th>Receipts</th>
          <th>Total</th>
        </tr>
      </thead>
      <tbody>
        {vendors.map((v) => (
          <tr key={v.vendor}>
            <td>{v.vendor}</td>
            <td>{v.count}</td>
            <td>{formatMoney(v.total)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
