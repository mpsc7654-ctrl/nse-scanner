import { create } from 'zustand'
import axios from 'axios'

const API = '/api/v1'

export interface StockSignal {
  symbol: string
  price: number
  change_pct: number
  volume: number
  signal: string
  confidence: number
  entry: number
  stoploss: number
  target1: number
  target2: number
  risk_reward: number
  option_strike: number
  option_type: string
  ema20: number
  ema100: number
  macd: number
  macd_signal: number
  rsi14: number
  atr: number
  vwap: number
  support1: number
  resistance1: number
  prev_day_high: number
  prev_day_low: number
  week_high: number
  week_low: number
  reasoning: string
}

export interface Breadth {
  strong_buy: number
  buy: number
  neutral: number
  sell: number
  strong_sell: number
  total: number
  advance_decline: number
}

interface ScannerStore {
  signals: StockSignal[]
  breadth: Breadth | null
  summary: string
  updatedAt: string | null
  loading: boolean
  error: string | null
  wsConnected: boolean
  filter: string
  search: string
  fetchSignals: () => Promise<void>
  fetchMarketData: () => Promise<void>
  setFilter: (f: string) => void
  setSearch: (s: string) => void
  updateSignal: (s: StockSignal) => void
  setWsConnected: (v: boolean) => void
  triggerScan: () => Promise<void>
}

export const useScannerStore = create<ScannerStore>((set, get) => ({
  signals: [],
  breadth: null,
  summary: '',
  updatedAt: null,
  loading: false,
  error: null,
  wsConnected: false,
  filter: 'ALL',
  search: '',

  fetchSignals: async () => {
    set({ loading: true, error: null })
    try {
      const { data } = await axios.get(`${API}/scanner/signals`)
      set({ signals: data.signals || [], updatedAt: data.updated_at, loading: false })
    } catch (e: any) {
      set({ error: e.message, loading: false })
    }
  },

  fetchMarketData: async () => {
    try {
      const { data } = await axios.get(`${API}/market/summary`)
      set({ breadth: data.breadth, summary: data.summary })
    } catch {}
  },

  setFilter: (f) => set({ filter: f }),
  setSearch: (s) => set({ search: s }),
  setWsConnected: (v) => set({ wsConnected: v }),

  updateSignal: (s) => {
    const signals = get().signals
    const idx = signals.findIndex(x => x.symbol === s.symbol)
    if (idx >= 0) {
      const updated = [...signals]
      updated[idx] = s
      set({ signals: updated })
    } else {
      set({ signals: [s, ...signals] })
    }
  },

  triggerScan: async () => {
    try {
      await axios.post(`${API}/scanner/trigger`)
    } catch {}
  },
}))

export const useFilteredSignals = () => {
  const { signals, filter, search } = useScannerStore()
  return signals.filter(s => {
    const matchFilter = filter === 'ALL' || s.signal === filter
    const matchSearch = !search || s.symbol.toLowerCase().includes(search.toLowerCase())
    return matchFilter && matchSearch
  })
}
