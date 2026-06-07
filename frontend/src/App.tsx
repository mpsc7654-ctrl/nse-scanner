import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { useEffect } from 'react'
import Sidebar from './components/layout/Sidebar'
import Dashboard from './pages/Dashboard'
import Scanner from './pages/Scanner'
import Watchlist from './pages/Watchlist'
import StockDetail from './pages/StockDetail'
import MarketBreadth from './pages/MarketBreadth'
import { useWebSocket } from './hooks/useWebSocket'
import { useScannerStore } from './stores/scannerStore'

function AppInner() {
  useWebSocket()
  const { fetchSignals, fetchMarketData } = useScannerStore()

  useEffect(() => {
    fetchSignals()
    fetchMarketData()
    // Refresh every 65s as fallback if WS misses
    const t = setInterval(() => {
      fetchSignals()
      fetchMarketData()
    }, 65000)
    return () => clearInterval(t)
  }, [])

  return (
    <div className="flex min-h-screen bg-[#0f1117]">
      <Sidebar />
      <main className="flex-1 overflow-auto">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/scanner" element={<Scanner />} />
          <Route path="/watchlist" element={<Watchlist />} />
          <Route path="/stock/:symbol" element={<StockDetail />} />
          <Route path="/breadth" element={<MarketBreadth />} />
        </Routes>
      </main>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AppInner />
    </BrowserRouter>
  )
}
