import { createContext, useCallback, useContext, useState } from 'react'
import { saveReceipt, uploadReceipt } from '../api/receipts'
import { normalizeItemsForSave } from '../utils/receiptMath'

const UploadContext = createContext(null)

// Mounted above the router (see App.jsx) so an in-progress analysis or an
// unsaved draft survives navigating to History/Analytics and back — it used
// to live as local state inside Dashboard.jsx, which React Router unmounts
// on every route change, silently discarding whatever was in progress.
export function UploadProvider({ children }) {
  const [selectedFile, setSelectedFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [status, setStatus] = useState(null)
  const [draft, setDraft] = useState(null)
  const [isSaving, setIsSaving] = useState(false)
  const [saveError, setSaveError] = useState('')
  const [refreshKey, setRefreshKey] = useState(0)

  function selectFile(file) {
    if (!file || !file.type.startsWith('image/')) return

    setSelectedFile(file)
    setStatus({ type: 'info', message: `${file.name} ready` })

    const reader = new FileReader()
    reader.onload = () => setPreviewUrl(reader.result)
    reader.readAsDataURL(file)
  }

  function clearSelection() {
    setSelectedFile(null)
    setPreviewUrl(null)
    setStatus(null)
  }

  const analyze = useCallback(async () => {
    if (!selectedFile) return

    setIsAnalyzing(true)
    setStatus({ type: 'info', message: 'Analyzing receipt...' })

    try {
      const data = await uploadReceipt(selectedFile)
      setStatus({ type: 'success', message: 'Review the extracted data, choose a category, then save or discard.' })
      setDraft(data)
      setSelectedFile(null)
      setPreviewUrl(null)
    } catch (err) {
      setStatus({ type: 'error', message: err.message || 'Could not reach server' })
    } finally {
      setIsAnalyzing(false)
    }
  }, [selectedFile])

  async function saveDraft(category, tripId) {
    if (!draft) return
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
        trip_id: tripId || null,
      })
      setDraft(null)
      setStatus(null)
      setRefreshKey((k) => k + 1)
    } catch (err) {
      setSaveError(err.message || 'Failed to save receipt')
    } finally {
      setIsSaving(false)
    }
  }

  function discardDraft() {
    setDraft(null)
    setStatus(null)
    setSaveError('')
  }

  function bumpRefresh() {
    setRefreshKey((k) => k + 1)
  }

  const value = {
    selectedFile,
    previewUrl,
    isAnalyzing,
    status,
    draft,
    isSaving,
    saveError,
    refreshKey,
    selectFile,
    clearSelection,
    analyze,
    saveDraft,
    discardDraft,
    bumpRefresh,
  }

  return <UploadContext.Provider value={value}>{children}</UploadContext.Provider>
}

export function useUpload() {
  const context = useContext(UploadContext)
  if (!context) {
    throw new Error('useUpload must be used inside UploadProvider')
  }
  return context
}
