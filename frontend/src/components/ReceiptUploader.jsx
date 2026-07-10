import { useRef, useState } from 'react'
import { useUpload } from '../receipts/UploadContext'

export default function ReceiptUploader() {
  const { selectedFile, previewUrl, isAnalyzing, status, selectFile, clearSelection, analyze } = useUpload()
  const fileInputRef = useRef(null)
  const [isDragOver, setIsDragOver] = useState(false)

  function resetSelection() {
    clearSelection()
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
          selectFile(e.dataTransfer.files?.[0])
        }}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          className="upload-zone-input"
          onChange={(e) => selectFile(e.target.files?.[0])}
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
          onClick={analyze}
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
