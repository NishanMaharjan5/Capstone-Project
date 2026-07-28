import { useEffect, useState } from 'react'
import { addIncome, deleteIncome, getIncome } from '../api/income'
import { formatMoney } from '../utils/receiptMath'

export default function Income() {
  const [items, setItems] = useState([])
  const [total, setTotal] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  const [amount, setAmount] = useState('')
  const [source, setSource] = useState('')
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10))
  const [formError, setFormError] = useState('')
  const [isSaving, setIsSaving] = useState(false)

  async function load() {
    setIsLoading(true)
    setError('')
    try {
      const data = await getIncome()
      setItems(data.items || [])
      setTotal(data.total || 0)
    } catch (err) {
      setError(err.message || 'Could not load income')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  async function handleSubmit(event) {
    event.preventDefault()
    setFormError('')

    const numericAmount = Number(amount)
    if (!numericAmount || numericAmount <= 0) {
      setFormError('Enter an amount greater than zero.')
      return
    }
    if (!source.trim()) {
      setFormError('Please enter a source.')
      return
    }

    setIsSaving(true)
    try {
      await addIncome({ amount: numericAmount, source: source.trim(), date })
      setAmount('')
      setSource('')
      await load()
    } catch (err) {
      setFormError(err.message || 'Could not save income')
    } finally {
      setIsSaving(false)
    }
  }

  async function handleDelete(id) {
    if (!window.confirm('Delete this income entry?')) return
    try {
      await deleteIncome(id)
      await load()
    } catch (err) {
      setError(err.message || 'Could not delete income')
    }
  }

  return (
    <section className="page-view">
      <div className="section-heading">
        <p className="eyebrow">Income</p>
        <h1>Track salary and other income</h1>
      </div>

      {error ? <div className="alert error">{error}</div> : null}

      <div className="grid lg:grid-cols-[360px_1fr] gap-6">
        <form onSubmit={handleSubmit} className="panel h-fit">
          <h2>Add income</h2>

          <label>
            Amount
            <input
              type="number"
              step="0.01"
              min="0"
              required
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="0.00"
            />
          </label>

          <label>
            Source
            <input
              required
              value={source}
              onChange={(e) => setSource(e.target.value)}
              placeholder="Salary, freelance, etc."
            />
          </label>

          <label>
            Date
            <input type="date" required value={date} onChange={(e) => setDate(e.target.value)} />
          </label>

          {formError ? <div className="alert error">{formError}</div> : null}

          <button type="submit" className="primary-button" disabled={isSaving}>
            {isSaving ? 'Saving...' : 'Add income'}
          </button>
        </form>

        <div className="panel">
          <h2>Income history</h2>
          <p className="total-spent">Total: {formatMoney(total)}</p>

          {isLoading ? (
            <p>Loading...</p>
          ) : items.length === 0 ? (
            <p>No income logged yet.</p>
          ) : (
            <div className="recent-list">
              {items.map((item) => (
                <div key={item.id} className="recent-card">
                  <div>
                    <strong>{item.source}</strong>
                    <p className="recent-meta">{item.date}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="font-bold text-mint-dark">+{formatMoney(item.amount)}</span>
                    <button type="button" className="link-button danger" onClick={() => handleDelete(item.id)}>
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </section>
  )
}
