import { useEffect, useState } from 'react'
import axios from 'axios'
import { useNavigate } from 'react-router-dom'
import { Plus, Star, X } from 'lucide-react'
import { useScannerStore } from '../stores/scannerStore'
import SignalBadge from '../components/ui/SignalBadge'

const API = '/api/v1'
const FNO = ['RELIANCE','TCS','HDFCBANK','INFY','ICICIBANK','SBIN','BHARTIARTL','KOTAKBANK','ITC','LT','AXISBANK','BAJFINANCE','TATAMOTORS','M&M','SUNPHARMA','WIPRO','HCLTECH']

export default function Watchlist() {
  const [watchlists, setWatchlists] = useState<any[]>([])
  const [active, setActive] = useState<any>(null)
  const [newName, setNewName] = useState('')
  const [adding, setAdding] = useState(false)
  const { signals } = useScannerStore()
  const navigate = useNavigate()

  const load = async () => {
    const { data } = await axios.get(`${API}/watchlists`)
    setWatchlists(data)
    if (data.length && !active) setActive(data[0])
  }

  useEffect(() => { load() }, [])

  const createList = async () => {
    if (!newName.trim()) return
    const { data } = await axios.post(`${API}/watchlists`, { name: newName, symbols: [] })
    setNewName('')
    setAdding(false)
    await load()
    setActive(data)
  }

  const addSymbol = async (symbol: string) => {
    if (!active || active.symbols.includes(symbol)) return
    const updated = { ...active, symbols: [...active.symbols, symbol] }
    await axios.put(`${API}/watchlists/${active.id}`, updated)
    setActive(updated)
    await load()
  }

  const removeSymbol = async (symbol: string) => {
    if (!active) return
    const updated = { ...active, symbols: active.symbols.filter((s: string) => s !== symbol) }
    await axios.put(`${API}/watchlists/${active.id}`, updated)
    setActive(updated)
    await load()
  }

  const watchSignals = active ? signals.filter(s => active.symbols.includes(s.symbol)) : []

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-lg font-semibold text-white">Watchlist</h1>

      <div className="grid grid-cols-4 gap-4">
        {/* Sidebar */}
        <div className="col-span-1 space-y-2">
          {watchlists.map(w => (
            <button key={w.id} onClick={() => setActive(w)}
              className={`w-full text-left px-3 py-2 rounded text-xs flex items-center gap-2 transition-colors ${active?.id === w.id ? 'bg-blue-900/40 text-blue-400' : 'text-slate-400 hover:bg-[#1e2535]'}`}>
              <Star size={12} />
              {w.name}
              <span className="ml-auto text-slate-600">{w.symbols.length}</span>
            </button>
          ))}

          {adding ? (
            <div className="flex gap-1">
              <input autoFocus value={newName} onChange={e => setNewName(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && createList()}
                className="flex-1 bg-[#161b27] border border-[#2a3347] rounded px-2 py-1 text-xs text-slate-300 outline-none"
                placeholder="List name" />
              <button onClick={createList} className="text-xs px-2 py-1 bg-blue-900/40 text-blue-400 rounded">+</button>
            </div>
          ) : (
            <button onClick={() => setAdding(true)}
              className="w-full text-left px-3 py-2 text-xs text-slate-600 hover:text-slate-400 flex items-center gap-2">
              <Plus size={12} /> New list
            </button>
          )}
        </div>

        {/* Main */}
        <div className="col-span-3 space-y-3">
          {active ? (
            <>
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-medium text-slate-300">{active.name}</h2>
                <span className="text-xs text-slate-500">{active.symbols.length} symbols</span>
              </div>

              {/* Add symbols */}
              <div className="flex flex-wrap gap-1.5">
                {FNO.filter(s => !active.symbols.includes(s)).map(s => (
                  <button key={s} onClick={() => addSymbol(s)}
                    className="text-[10px] px-2 py-1 border border-[#2a3347] rounded text-slate-500 hover:border-blue-700 hover:text-blue-400 transition-colors">
                    + {s}
                  </button>
                ))}
              </div>

              {/* Signals for watchlist */}
              <div className="bg-[#161b27] border border-[#2a3347] rounded-lg overflow-hidden">
                {active.symbols.length === 0 ? (
                  <p className="text-center py-8 text-xs text-slate-600">Add symbols above to track them</p>
                ) : (
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="text-slate-500 border-b border-[#2a3347]">
                        <th className="px-3 py-2 text-left">Symbol</th>
                        <th className="px-3 py-2 text-left">Price</th>
                        <th className="px-3 py-2 text-left">Change</th>
                        <th className="px-3 py-2 text-left">Signal</th>
                        <th className="px-3 py-2 text-left">RSI</th>
                        <th className="px-3 py-2 text-left">Target 1</th>
                        <th className="px-3 py-2 text-left"></th>
                      </tr>
                    </thead>
                    <tbody>
                      {active.symbols.map((sym: string) => {
                        const sig = watchSignals.find(s => s.symbol === sym)
                        return (
                          <tr key={sym} className="table-row border-b border-[#1e2535] cursor-pointer" onClick={() => navigate(`/stock/${sym}`)}>
                            <td className="px-3 py-2 font-mono font-medium text-white">{sym}</td>
                            <td className="px-3 py-2 font-mono">{sig ? `₹${sig.price?.toLocaleString()}` : '—'}</td>
                            <td className={`px-3 py-2 font-mono ${(sig?.change_pct ?? 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                              {sig ? `${sig.change_pct >= 0 ? '+' : ''}${sig.change_pct?.toFixed(2)}%` : '—'}
                            </td>
                            <td className="px-3 py-2">{sig ? <SignalBadge signal={sig.signal} /> : '—'}</td>
                            <td className="px-3 py-2 font-mono text-slate-400">{sig?.rsi14?.toFixed(1) ?? '—'}</td>
                            <td className="px-3 py-2 font-mono text-green-400">{sig ? `₹${sig.target1?.toFixed(0)}` : '—'}</td>
                            <td className="px-3 py-2">
                              <button onClick={e => { e.stopPropagation(); removeSymbol(sym) }}
                                className="text-slate-600 hover:text-red-400 transition-colors">
                                <X size={12} />
                              </button>
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                )}
              </div>
            </>
          ) : (
            <p className="text-xs text-slate-600 py-8 text-center">Create a watchlist to start tracking symbols</p>
          )}
        </div>
      </div>
    </div>
  )
}
