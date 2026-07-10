import { useAuth } from '../auth/AuthContext'
import DashboardInsights from '../components/DashboardInsights'
import ExtractedReceiptReview from '../components/ExtractedReceiptReview'
import ManualReceiptForm from '../components/ManualReceiptForm'
import ReceiptUploader from '../components/ReceiptUploader'
import RecentReceipts from '../components/RecentReceipts'
import { useUpload } from '../receipts/UploadContext'

function getGreeting() {
  const hour = new Date().getHours()
  if (hour < 12) return 'Good morning'
  if (hour < 18) return 'Good afternoon'
  return 'Good evening'
}

export default function Dashboard() {
  const { user } = useAuth()
  const { draft, refreshKey, bumpRefresh } = useUpload()
  const firstName = (user?.name || 'there').split(' ')[0]

  return (
    <section className="page-view">
      <div className="section-heading">
        <p className="eyebrow">Dashboard</p>
        <h1>
          {getGreeting()}, {firstName}
        </h1>
        <p>Here's how your spending is looking.</p>
      </div>

      <DashboardInsights refreshKey={refreshKey} />

      {!draft ? <ReceiptUploader /> : <ExtractedReceiptReview />}

      <ManualReceiptForm onSaved={bumpRefresh} />

      <RecentReceipts refreshKey={refreshKey} />
    </section>
  )
}
