import { Routes, Route, useLocation } from 'react-router-dom'
import { AnimatePresence } from 'framer-motion'
import { Sidebar } from '@/components/layout/Sidebar'
import { GeneratePage } from '@/pages/GeneratePage'
import { CaptionsPage } from '@/pages/CaptionsPage'
import { HistoryPage } from '@/pages/HistoryPage'
import { ToolsPage } from '@/pages/ToolsPage'
import { PresetsPage } from '@/pages/PresetsPage'
import { DashboardPage } from '@/pages/DashboardPage'
import { ReviewPage } from '@/pages/ReviewPage'
import { CurationPage } from '@/pages/CurationPage'
import { SchedulingPage } from '@/pages/SchedulingPage'
import { AccountSettingsPage } from '@/pages/AccountSettingsPage'
import { PromptsPage } from '@/pages/PromptsPage'

export default function App() {
  const location = useLocation()

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        {/* Background gradient */}
        <div className="pointer-events-none fixed inset-0 z-0">
          <div className="absolute top-[-20%] left-[30%] h-[500px] w-[500px] rounded-full bg-accent-glow blur-[120px]" />
          <div className="absolute bottom-[-10%] right-[20%] h-[400px] w-[400px] rounded-full bg-accent-glow blur-[120px]" />
        </div>

        <div className="relative z-10">
          <AnimatePresence mode="wait">
            <Routes location={location} key={location.pathname}>
              <Route path="/" element={<GeneratePage />} />
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/review" element={<ReviewPage />} />
              <Route path="/curation" element={<CurationPage />} />
              <Route path="/scheduling" element={<SchedulingPage />} />
              <Route path="/settings" element={<AccountSettingsPage />} />
              <Route path="/captions" element={<CaptionsPage />} />
              <Route path="/history" element={<HistoryPage />} />
              <Route path="/prompts" element={<PromptsPage />} />
              <Route path="/tools" element={<ToolsPage />} />
              <Route path="/presets" element={<PresetsPage />} />
            </Routes>
          </AnimatePresence>
        </div>
      </main>
    </div>
  )
}
