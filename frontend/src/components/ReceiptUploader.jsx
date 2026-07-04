import { useRef, useState } from 'react'
import { uploadReceipt } from '../api/receipts'

export default function ReceiptUploader({ onAnalyzed }) {
  const fileInputRef = useRef(null)
  const [selectedFile, setSelectedFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState(null)
  const [isDragOver, setIsDragOver] = useState(false)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [status, setStatus] = useState(null)

  function handleFile(file) {
    if (!file || !file.type.startsWith('image/')) return

    setSelectedFile(file)
    setStatus({ type: 'info', message: `${file.name} ready` })

    const reader = new FileReader()
    reader.onload = () => setPreviewUrl(reader.result)
    reader.readAsDataURL(file)
  }

  async function handleAnalyze() {
    if (!selectedFile) return

    setIsAnalyzing(true)
    setStatus({ type: 'info', message: 'Analyzing receipt...' })

    try {
      const data = await uploadReceipt(selectedFile)
      setStatus({ type: 'success', message: 'Review the extracted data, choose a category, then save or discard.' })
      onAnalyzed(data)
    } catch (err) {
      setStatus({ type: 'error', message: err.message || 'Could not reach server' })
    } finally {
      setIsAnalyzing(false)
    }
  }

  function resetSelection() {
    setSelectedFile(null)
    setPreviewUrl(null)
    setStatus(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  return (
    <div className="panel">
      <h2>Upload a receipt</h2>

      <div
        className={`upload-zone${isDragOver ? ' drag-over' : ''}`}
        onDragOver={(e) => {
          e.preventDefault()
          setIsDragOver(true)
        }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={(e) => {
          e.preventDefault()
          setIsDragOver(false)
          handleFile(e.dataTransfer.files?.[0])
        }}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          className="upload-zone-input"
          onChange={(e) => handleFile(e.target.files?.[0])}
        />
        <p>Drag and drop an image here, or click to choose a file</p>
      </div>

      {previewUrl ? (
        <div className="preview-wrap">
          <img src={previewUrl} alt="Receipt preview" className="preview-image" />
        </div>
      ) : null}

      {status ? <div className={`alert ${status.type}`}>{status.message}</div> : null}

      <div className="button-row">
        <button
          type="button"
          className="primary-button"
          disabled={!selectedFile || isAnalyzing}
          onClick={handleAnalyze}
        >
          {isAnalyzing ? 'Analyzing...' : 'Analyze Receipt'}
        </button>
        {selectedFile ? (
          <button type="button" className="secondary-button" onClick={resetSelection} disabled={isAnalyzing}>
            Clear
          </button>
        ) : null}
      </div>
    </div>
  )
}
