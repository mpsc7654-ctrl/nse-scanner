import { useEffect } from 'react'
import { useScannerStore, useFilteredSignals } from '../stores/scannerStore'
import ScannerTable from '../components/ScannerTable'
import { Search } from 'lucide-react'

const FILTERS = ['ALL', 'STRONG_BUY', 'BUY', 'NEUTRAL', 'SELL', 'STRONG_SELL']
const FILTER_LABELS: Record<string, string> = {
  ALL: 'All', STRONG_BUY: '⬆ Strong Buy', BUY: '↑ Buy',
  NEUTRAL: '→ Neutral', SELL: '↓ Sell', STRONG_SELL: '⬇ Sell'
}
const FILTER_COLORS: Record<string, string> = {
  ALL: 'text-slate-400', STRONG_BUY: 'text-green-400', BUY: 'text-green-300',
  NEUTRAL: 'text-slate-400', SELL: 'text-red-300', STRONG_SELL: 'text-red-400'
}

export default function Scanner() {
  const { filter, search, setFilter, setSearch, fetchSignals, loading } = useScannerStore()
  const signals = useFilteredSignals()

  useEffect(() => { fetchSignals() }, [])

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-white">Scanner</h1>
          <p className="text-xs text-slate-500">{signals.length} signals · Updates every 60s</p>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="flex gap-1 bg-[#161b27] border border-[#2a3347] rounded-lg p-1">
          {FILTERS.map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1.5 rounded text-xs transition-colors ${
                filter === f
                  ? 'bg-[#2a3347] text-white'
                  : `${FILTER_COLORS[f]} hover:bg-[#1e2535]`
              }`}
            >
              {FILTER_LABELS[f]}
            </button>
          ))}
        </div>

        <div className="relative">
          <Search size={12} className="absolute left-2.5 top-2.5 text-slate-500" />
          <input
            type="text"
            placeholder="Search symbol..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="bg-[#161b27] border border-[#2a3347] rounded pl-7 pr-3 py-1.5 text-xs text-slate-300 placeholder-slate-600 outline-none focus:border-blue-700 w-40"
          />
        </div>
      </div>

      {/* Table */}
      <div className="bg-[#161b27] border border-[#2a3347] rounded-lg">
        {loading && (
          <div className="text-center py-4 text-xs text-slate-500">Loading...</div>
        )}
        <ScannerTable signals={signals} />
      </div>
    </div>
  )
}
