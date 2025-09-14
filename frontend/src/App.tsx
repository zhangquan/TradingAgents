import { Routes, Route } from 'react-router-dom'
import { Navigation } from '@/components/navigation'
import { Toaster } from '@/components/ui/sonner'

// 导入页面组件
import HomePage from '@/pages/page'
import AdminPage from '@/pages/admin/page'
import AnalysisPage from '@/pages/analysis/page'
import ChartsPage from '@/pages/charts-demo/page'
import ReportsPage from '@/pages/reports/page'
import ReportDetailPage from '@/pages/reports/[id]/page'
import SettingsPage from '@/pages/settings/page'
import WatchlistPage from '@/pages/watchlist/page'

function App() {
  return (
    <div className="flex h-full bg-gray-50">
      <Navigation />
      <main className="flex-1 lg:ml-0 pt-16 lg:pt-0 overflow-auto">
        <div className="p-6">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/admin" element={<AdminPage />} />
            <Route path="/analysis" element={<AnalysisPage />} />
            <Route path="/charts-demo" element={<ChartsPage />} />
            <Route path="/reports" element={<ReportsPage />} />
            <Route path="/reports/:id" element={<ReportDetailPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/watchlist" element={<WatchlistPage />} />
          </Routes>
        </div>
      </main>
      <Toaster />
    </div>
  )
}

export default App
