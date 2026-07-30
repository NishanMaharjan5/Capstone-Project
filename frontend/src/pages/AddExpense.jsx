import { useNavigate } from 'react-router-dom'
import ManualReceiptForm from '../components/ManualReceiptForm'

export default function AddExpense() {
  const navigate = useNavigate()

  async function handleSaved() {
    navigate('/')
  }

  return (
    <section className="page-view">
      <div className="section-heading">
        <p className="eyebrow">Add expense</p>
        <h1>Log a manual entry</h1>
        <p>Add a receipt by hand — vendor, items, and category.</p>
      </div>

      <ManualReceiptForm onSaved={handleSaved} defaultOpen />
    </section>
  )
}
