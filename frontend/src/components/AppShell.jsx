import { Link } from 'react-router-dom'
import Sidebar from './Sidebar'
import BottomNav from './BottomNav'
import { useUpload } from '../receipts/UploadContext'

function UploadStatusBanner() {
  const { isAnalyzing, draft } = useUpload()

  if (isAnalyzing) {
    return <div className="status-banner">Analyzing receipt...</div>
  }
  if (draft) {
    return (
      <Link to="/scan" className="status-banner">
        Receipt ready to review →
      </Link>
    )
  }
  return null
}

export default function AppShell({ children }) {
  return (
    <div className="min-h-screen bg-cream flex">
      <Sidebar />
      <div className="flex-1 min-w-0">
        <main className="px-4 sm:px-6 lg:px-10 pt-6 pb-28 lg:pb-10">
          <UploadStatusBanner />
          {children}
        </main>
      </div>
      <BottomNav />
    </div>
  )
}
