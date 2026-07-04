import { useState } from 'react'
import ExtractedReceiptReview from '../components/ExtractedReceiptReview'
import ManualReceiptForm from '../components/ManualReceiptForm'
import ReceiptUploader from '../components/ReceiptUploader'
import RecentReceipts from '../components/RecentReceipts'
import { saveReceipt } from '../api/receipts'
import { normalizeItemsForSave } from '../utils/receiptMath'

export default function Dashboard() {
  const [draft, setDraft] = useState(null)
  const [isSaving, setIsSaving] = useState(false)
  const [saveError, setSaveError] = useState('')
  const [refreshKey, setRefreshKey] = useState(0)

  async function handleSave(category) {
    const extracted = draft.extracted_data || {}
    setIsSaving(true)
    setSaveError('')

    try {
      await saveReceipt({
        vendor: extracted.vendor || null,
        date: extracted.date || null,
        total: extracted.total == null ? null : Number(extracted.total),
        category,
        items: normalizeItemsForSave(extracted.items),
        verified: Boolean(extracted.verified),
        raw_text: draft.raw_text || [],
      })
      setDraft(null)
      setRefreshKey((k) => k + 1)
    } catch (err) {
      setSaveError(err.message || 'Failed to save receipt')
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <section className="page-view">
      <div className="section-heading">
        <p className="eyebrow">Dashboard</p>
        <h1>Upload a receipt</h1>
        <p>Analyze a receipt image, review the extracted data, then save or discard it.</p>
      </div>

      {!draft ? (
        <ReceiptUploader onAnalyzed={setDraft} />
      ) : (
        <ExtractedReceiptReview
          draft={draft}
          onSave={handleSave}
          onDiscard={() => setDraft(null)}
          isSaving={isSaving}
          saveError={saveError}
        />
      )}

      <ManualReceiptForm onSaved={() => setRefreshKey((k) => k + 1)} />

      <RecentReceipts refreshKey={refreshKey} />
    </section>
  )
}
