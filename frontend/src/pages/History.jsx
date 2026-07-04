import { useCallback, useEffect, useState } from 'react'
import ReceiptTable from '../components/ReceiptTable'
import { deleteReceipt, getReceipts } from '../api/receipts'

export default function History() {
  const [receipts, setReceipts] = useState([])
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(true)

  const loadReceipts = useCallback(async () => {
    setIsLoading(true)
    setError('')

    try {
      const data = await getReceipts()
      setReceipts(data.receipts || [])
    } catch (err) {
      setError(err.message || 'Could not load receipts')
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    loadReceipts()
  }, [loadReceipts])

  async function handleDelete(id) {
    await deleteReceipt(id)
    setReceipts((prev) => prev.filter((r) => r._id !== id))
  }

  return (
    <section className="page-view">
      <div className="section-heading">
        <p className="eyebrow">Protected route</p>
        <h1>Receipt history</h1>
      </div>

      {error ? <div className="alert error">{error}</div> : null}

      {isLoading ? <p>Loading receipts...</p> : <ReceiptTable receipts={receipts} onDelete={handleDelete} />}
    </section>
  )
}
