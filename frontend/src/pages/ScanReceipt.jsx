import ExtractedReceiptReview from '../components/ExtractedReceiptReview'
import ReceiptUploader from '../components/ReceiptUploader'
import { useUpload } from '../receipts/UploadContext'

export default function ScanReceipt() {
  const { draft } = useUpload()

  return (
    <section className="page-view">
      <div className="section-heading">
        <p className="eyebrow">Scan receipt</p>
        <h1>Bill scanner</h1>
        <p>Upload a photo and we'll pull out the vendor, date, total, and items.</p>
      </div>

      {!draft ? <ReceiptUploader /> : <ExtractedReceiptReview />}
    </section>
  )
}
