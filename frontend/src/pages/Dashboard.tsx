import { useEffect } from 'react'
import { useScannerStore } from '../stores/scannerStore'
import SignalBadge from '../components/ui/SignalBadge'
import ScannerTable from '../components/ScannerTable'
import { useNavigate } from 'react-router-dom'
import { RefreshCw, Brain } from 'lucide-react'

export default function Dashboard() {
  const { breadth, summary, signals, fetchSignals, fetchMarketData, loading, triggerScan } = useScannerStore()
  const navigate = useNavigate()

  useEffect(() => {
    fetchSignals()
    fetchMarketData()
  }, [])

  const topBuys = signals.filter(s => s.signal === 'STRONG_BUY').slice(0, 5)
  const topSells = signals.filter(s => s.signal === 'STRONG_SELL').slice(0, 5)

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-white">Dashboard</h1>
          <p className="text-xs text-slate-500">NSE F&O Scanner — Live</p>
        </div>
        <button
          onClick={triggerScan}
          className="flex items-center gap-2 px-3 py-1.5 text-xs bg-blue-900/40 hover:bg-blue-900/60 text-blue-400 rounded border border-blue-800/50 transition-colors"
        >
          <RefreshCw size={12} className={loading ? 'animate-spin' : ''} />
          Refresh Scan
        </button>
      </div>

      {/* Breadth Cards */}
      {breadth && (
        <div className="grid grid-cols-5 gap-3">
          {[
            { label: 'Strong Buy', key: 'strong_buy', cls: 'text-green-400' },
            { label: 'Buy', key: 'buy', cls: 'text-green-300' },
            { label: 'Neutral', key: 'neutral', cls: 'text-slate-400' },
            { label: 'Sell', key: 'sell', cls: 'text-red-300' },
            { label: 'Strong Sell', key: 'strong_sell', cls: 'text-red-400' },
          ].map(({ label, key, cls }) => (
            <div key={key} className="bg-[#161b27] border border-[#2a3347] rounded-lg p-4">
              <p className="text-[10px] text-slate-500 mb-1">{label}</p>
              <p className={`text-2xl font-mono font-medium ${cls}`}>{(breadth as any)[key]}</p>
              <p className="text-[10px] text-slate-600 mt-1">of {breadth.total}</p>
            </div>
          ))}
        </div>
      )}

      {/* AI Summary */}
      {summary && (
        <div className="bg-[#161b27] border border-[#2a3347] rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <Brain size={14} className="text-purple-400" />
            <span className="text-xs text-purple-400 font-medium">Market Intelligence</span>
          </div>
          <p className="text-sm text-slate-300 leading-relaxed">{summary}</p>
        </div>
      )}

      {/* Top Signals Grid */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-[#161b27] border border-[#2a3347] rounded-lg p-4">
          <h3 className="text-xs font-medium text-green-400 mb-3">Top Strong Buy</h3>
          <div className="space-y-2">
            {topBuys.map(s => (
              <div
                key={s.symbol}
                onClick={() => navigate(`/stock/${s.symbol}`)}
                className="flex items-center justify-between cursor-pointer hover:bg-[#1e2535] px-2 py-1.5 rounded transition-colors"
              >
                <span className="font-mono text-sm text-white">{s.symbol}</span>
                <div className="flex items-center gap-3">
                  <span className="text-xs font-mono text-slate-400">₹{s.price?.toLocaleString()}</span>
                  <span className="text-xs text-green-400">{s.confidence?.toFixed(0)}%</span>
                  <span className="text-xs font-mono text-slate-500">RR {s.risk_reward?.toFixed(1)}</span>
                </div>
              </div>
            ))}
            {topBuys.length === 0 && <p className="text-xs text-slate-600">No strong buy signals</p>}
          </div>
        </div>

        <div className="bg-[#161b27] border border-[#2a3347] rounded-lg p-4">
          <h3 className="text-xs font-medium text-red-400 mb-3">Top Strong Sell</h3>
          <div className="space-y-2">
            {topSells.map(s => (
              <div
                key={s.symbol}
                onClick={() => navigate(`/stock/${s.symbol}`)}
                className="flex items-center justify-between cursor-pointer hover:bg-[#1e2535] px-2 py-1.5 rounded transition-colors"
              >
                <span className="font-mono text-sm text-white">{s.symbol}</span>
                <div className="flex items-center gap-3">
                  <span className="text-xs font-mono text-slate-400">₹{s.price?.toLocaleString()}</span>
                  <span className="text-xs text-red-400">{s.confidence?.toFixed(0)}%</span>
                  <span className="text-xs font-mono text-slate-500">RR {s.risk_reward?.toFixed(1)}</span>
                </div>
              </div>
            ))}
            {topSells.length === 0 && <p className="text-xs text-slate-600">No strong sell signals</p>}
          </div>
        </div>
      </div>

      {/* Recent Signals Table */}
      <div className="bg-[#161b27] border border-[#2a3347] rounded-lg">
        <div className="px-4 py-3 border-b border-[#2a3347]">
          <h3 className="text-xs font-medium text-slate-300">All Signals</h3>
        </div>
        <ScannerTable signals={signals.slice(0, 15)} />
      </div>
    </div>
  )
}
