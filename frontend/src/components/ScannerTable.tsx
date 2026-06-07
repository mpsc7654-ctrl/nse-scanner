import { useNavigate } from 'react-router-dom'
import { StockSignal } from '../stores/scannerStore'
import SignalBadge from './ui/SignalBadge'
import { TrendingUp, TrendingDown } from 'lucide-react'

interface Props { signals: StockSignal[] }

const fmt = (n: number) => n?.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
const fmtVol = (n: number) => n >= 1e7 ? `${(n/1e7).toFixed(1)}Cr` : n >= 1e5 ? `${(n/1e5).toFixed(1)}L` : `${n}`

export default function ScannerTable({ signals }: Props) {
  const navigate = useNavigate()

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr className="text-slate-500 border-b border-[#2a3347]">
            {['Symbol','Price','Change','Signal','Confidence','Entry','Stoploss','Target 1','Target 2','R:R','RSI','Volume','Option'].map(h => (
              <th key={h} className="px-3 py-2 text-left font-medium whitespace-nowrap">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {signals.map(s => (
            <tr
              key={s.symbol}
              className="table-row border-b border-[#1e2535] cursor-pointer"
              onClick={() => navigate(`/stock/${s.symbol}`)}
            >
              <td className="px-3 py-2 font-mono font-medium text-white">{s.symbol}</td>
              <td className="px-3 py-2 font-mono">₹{fmt(s.price)}</td>
              <td className={`px-3 py-2 font-mono flex items-center gap-1 ${s.change_pct >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {s.change_pct >= 0 ? <TrendingUp size={11} /> : <TrendingDown size={11} />}
                {s.change_pct?.toFixed(2)}%
              </td>
              <td className="px-3 py-2">
                <SignalBadge signal={s.signal} />
              </td>
              <td className="px-3 py-2">
                <div className="flex items-center gap-2">
                  <div className="w-16 bg-[#1e2535] rounded-full h-1">
                    <div
                      className="h-1 rounded-full"
                      style={{
                        width: `${s.confidence}%`,
                        background: s.confidence >= 75 ? '#00d084' : s.confidence >= 55 ? '#f59e0b' : '#94a3b8'
                      }}
                    />
                  </div>
                  <span className="text-slate-400">{s.confidence?.toFixed(0)}%</span>
                </div>
              </td>
              <td className="px-3 py-2 font-mono text-blue-400">₹{fmt(s.entry)}</td>
              <td className="px-3 py-2 font-mono text-red-400">₹{fmt(s.stoploss)}</td>
              <td className="px-3 py-2 font-mono text-green-400">₹{fmt(s.target1)}</td>
              <td className="px-3 py-2 font-mono text-green-300">₹{fmt(s.target2)}</td>
              <td className="px-3 py-2 font-mono">{s.risk_reward?.toFixed(2)}</td>
              <td className={`px-3 py-2 font-mono ${s.rsi14 > 70 ? 'text-red-400' : s.rsi14 < 30 ? 'text-green-400' : 'text-slate-300'}`}>
                {s.rsi14?.toFixed(1)}
              </td>
              <td className="px-3 py-2 font-mono text-slate-400">{fmtVol(s.volume)}</td>
              <td className="px-3 py-2">
                <span className={`font-mono text-[10px] px-1.5 py-0.5 rounded ${s.option_type === 'CE' ? 'bg-green-900/40 text-green-400' : 'bg-red-900/40 text-red-400'}`}>
                  {s.option_strike} {s.option_type}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {signals.length === 0 && (
        <div className="text-center py-16 text-slate-500">
          No signals match the current filter. Scan running every 60s.
        </div>
      )}
    </div>
  )
}
