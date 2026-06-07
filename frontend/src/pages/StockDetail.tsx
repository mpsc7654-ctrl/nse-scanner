import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import axios from 'axios'
import { ArrowLeft, Brain } from 'lucide-react'
import SignalBadge from '../components/ui/SignalBadge'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'

const API = '/api/v1'
const fmt = (n: number) => n?.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

export default function StockDetail() {
  const { symbol } = useParams()
  const navigate = useNavigate()
  const [data, setData] = useState<any>(null)
  const [history, setHistory] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!symbol) return
    Promise.all([
      axios.get(`${API}/stock/${symbol}/detail`),
      axios.get(`${API}/stock/${symbol}/history?days=30`)
    ]).then(([d, h]) => {
      setData(d.data)
      setHistory(h.data.data?.map((r: any) => ({ time: new Date(r.ts).toLocaleDateString('en-IN', {day:'2-digit',month:'short'}), price: r.price, volume: r.volume })) ?? [])
    }).catch(() => {}).finally(() => setLoading(false))
  }, [symbol])

  if (loading) return <div className="p-6 text-slate-500 text-sm">Loading...</div>
  if (!data) return <div className="p-6 text-slate-500 text-sm">Data unavailable. Ensure scan has run.</div>

  return (
    <div className="p-6 space-y-5">
      <button onClick={() => navigate(-1)} className="flex items-center gap-2 text-xs text-slate-400 hover:text-white transition-colors">
        <ArrowLeft size={14} /> Back
      </button>

      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-mono font-semibold text-white">{symbol}</h1>
          <div className="flex items-center gap-3 mt-1">
            <span className="text-xl font-mono text-slate-200">₹{fmt(data.price)}</span>
            <span className={`text-sm font-mono ${data.change_pct >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {data.change_pct >= 0 ? '+' : ''}{data.change_pct?.toFixed(2)}%
            </span>
          </div>
        </div>
        <div className="text-right">
          <SignalBadge signal={data.signal} size="md" />
          <p className="text-xs text-slate-500 mt-1">Confidence: {data.confidence?.toFixed(0)}%</p>
        </div>
      </div>

      {/* AI Summary */}
      {data.ai_summary && (
        <div className="bg-[#161b27] border border-[#2a3347] rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <Brain size={14} className="text-purple-400" />
            <span className="text-xs text-purple-400 font-medium">AI Analysis</span>
          </div>
          <p className="text-sm text-slate-300 leading-relaxed">{data.ai_summary}</p>
        </div>
      )}

      {/* Trade Setup */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { label: 'Entry', value: `₹${fmt(data.entry)}`, cls: 'text-blue-400' },
          { label: 'Stoploss', value: `₹${fmt(data.stoploss)}`, cls: 'text-red-400' },
          { label: 'Target 1', value: `₹${fmt(data.target1)}`, cls: 'text-green-400' },
          { label: 'Target 2', value: `₹${fmt(data.target2)}`, cls: 'text-green-300' },
        ].map(({ label, value, cls }) => (
          <div key={label} className="bg-[#161b27] border border-[#2a3347] rounded-lg p-3">
            <p className="text-[10px] text-slate-500 mb-1">{label}</p>
            <p className={`text-lg font-mono font-medium ${cls}`}>{value}</p>
          </div>
        ))}
      </div>

      {/* Price Chart */}
      {history.length > 1 && (
        <div className="bg-[#161b27] border border-[#2a3347] rounded-lg p-4">
          <p className="text-xs text-slate-400 mb-3">Price — 30 days</p>
          <ResponsiveContainer width="100%" height={180}>
            <LineChart data={history}>
              <XAxis dataKey="time" tick={{ fill: '#64748b', fontSize: 10 }} tickLine={false} />
              <YAxis tick={{ fill: '#64748b', fontSize: 10 }} tickLine={false} domain={['auto', 'auto']} width={60} />
              <Tooltip
                contentStyle={{ background: '#161b27', border: '1px solid #2a3347', borderRadius: 6, fontSize: 11 }}
                formatter={(v: any) => [`₹${v?.toFixed(2)}`, 'Price']}
              />
              <ReferenceLine y={data.support1} stroke="#ff4d4d" strokeDasharray="3 3" strokeWidth={1} />
              <ReferenceLine y={data.resistance1} stroke="#00d084" strokeDasharray="3 3" strokeWidth={1} />
              <ReferenceLine y={data.ema100} stroke="#3b82f6" strokeDasharray="2 4" strokeWidth={1} />
              <Line type="monotone" dataKey="price" stroke="#3b82f6" dot={false} strokeWidth={1.5} />
            </LineChart>
          </ResponsiveContainer>
          <div className="flex gap-4 mt-2">
            <span className="text-[10px] text-red-400">— Support ₹{fmt(data.support1)}</span>
            <span className="text-[10px] text-green-400">— Resistance ₹{fmt(data.resistance1)}</span>
            <span className="text-[10px] text-blue-400">— EMA100 ₹{fmt(data.ema100)}</span>
          </div>
        </div>
      )}

      {/* Indicators Grid */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { label: 'EMA 20', value: `₹${fmt(data.ema20)}` },
          { label: 'EMA 100', value: `₹${fmt(data.ema100)}` },
          { label: 'MACD', value: data.macd?.toFixed(3) },
          { label: 'Signal', value: data.macd_signal?.toFixed(3) },
          { label: 'RSI 14', value: data.rsi14?.toFixed(1), cls: data.rsi14 > 70 ? 'text-red-400' : data.rsi14 < 30 ? 'text-green-400' : 'text-slate-200' },
          { label: 'ATR', value: `₹${fmt(data.atr)}` },
          { label: 'VWAP', value: `₹${fmt(data.vwap)}` },
          { label: 'Risk/Reward', value: `${data.risk_reward?.toFixed(2)}x` },
        ].map(({ label, value, cls }) => (
          <div key={label} className="bg-[#161b27] border border-[#2a3347] rounded p-3">
            <p className="text-[10px] text-slate-500 mb-1">{label}</p>
            <p className={`text-sm font-mono ${cls ?? 'text-slate-200'}`}>{value}</p>
          </div>
        ))}
      </div>

      {/* Support/Resistance */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-[#161b27] border border-[#2a3347] rounded-lg p-4">
          <p className="text-xs text-slate-400 mb-3">Support Levels</p>
          <div className="space-y-1.5">
            {[data.support1, data.support2].filter(Boolean).map((v, i) => (
              <div key={i} className="flex justify-between items-center">
                <span className="text-[10px] text-slate-500">S{i + 1}</span>
                <span className="font-mono text-sm text-red-300">₹{fmt(v)}</span>
              </div>
            ))}
            <div className="flex justify-between items-center">
              <span className="text-[10px] text-slate-500">Prev Day Low</span>
              <span className="font-mono text-sm text-red-300">₹{fmt(data.prev_day_low)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-[10px] text-slate-500">Week Low</span>
              <span className="font-mono text-sm text-red-300">₹{fmt(data.week_low)}</span>
            </div>
          </div>
        </div>
        <div className="bg-[#161b27] border border-[#2a3347] rounded-lg p-4">
          <p className="text-xs text-slate-400 mb-3">Resistance Levels</p>
          <div className="space-y-1.5">
            {[data.resistance1, data.resistance2].filter(Boolean).map((v, i) => (
              <div key={i} className="flex justify-between items-center">
                <span className="text-[10px] text-slate-500">R{i + 1}</span>
                <span className="font-mono text-sm text-green-300">₹{fmt(v)}</span>
              </div>
            ))}
            <div className="flex justify-between items-center">
              <span className="text-[10px] text-slate-500">Prev Day High</span>
              <span className="font-mono text-sm text-green-300">₹{fmt(data.prev_day_high)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-[10px] text-slate-500">Week High</span>
              <span className="font-mono text-sm text-green-300">₹{fmt(data.week_high)}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Option Recommendation */}
      <div className="bg-[#161b27] border border-[#2a3347] rounded-lg p-4">
        <p className="text-xs text-slate-400 mb-3">Option Recommendation</p>
        <div className="flex items-center gap-4">
          <span className={`text-2xl font-mono font-semibold ${data.option_type === 'CE' ? 'text-green-400' : 'text-red-400'}`}>
            {data.option_strike} {data.option_type}
          </span>
          <span className="text-xs text-slate-500">
            {data.option_type === 'CE' ? 'Buy Call' : 'Buy Put'} at nearest strike
          </span>
        </div>
      </div>

      {/* Reasoning */}
      {data.reasoning && (
        <div className="bg-[#161b27] border border-[#2a3347] rounded-lg p-4">
          <p className="text-xs text-slate-400 mb-2">Signal Reasoning</p>
          <div className="flex flex-wrap gap-2">
            {data.reasoning.split(' | ').map((r: string) => (
              <span key={r} className="text-[10px] px-2 py-1 bg-[#1e2535] rounded text-slate-300">{r}</span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
