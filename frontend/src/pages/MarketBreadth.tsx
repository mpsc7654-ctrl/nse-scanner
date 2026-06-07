import { useEffect, useState } from 'react'
import { useScannerStore } from '../stores/scannerStore'
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, BarChart, Bar, XAxis, YAxis } from 'recharts'

const COLORS = ['#00d084', '#34d399', '#94a3b8', '#f87171', '#ff4d4d']

export default function MarketBreadth() {
  const { breadth, fetchMarketData, signals } = useScannerStore()

  useEffect(() => { fetchMarketData() }, [])

  const pieData = breadth ? [
    { name: 'Strong Buy', value: breadth.strong_buy },
    { name: 'Buy', value: breadth.buy },
    { name: 'Neutral', value: breadth.neutral },
    { name: 'Sell', value: breadth.sell },
    { name: 'Strong Sell', value: breadth.strong_sell },
  ] : []

  // RSI distribution
  const rsiData = [
    { range: '<30', count: signals.filter(s => s.rsi14 < 30).length, fill: '#00d084' },
    { range: '30-40', count: signals.filter(s => s.rsi14 >= 30 && s.rsi14 < 40).length, fill: '#34d399' },
    { range: '40-60', count: signals.filter(s => s.rsi14 >= 40 && s.rsi14 < 60).length, fill: '#94a3b8' },
    { range: '60-70', count: signals.filter(s => s.rsi14 >= 60 && s.rsi14 < 70).length, fill: '#f87171' },
    { range: '>70', count: signals.filter(s => s.rsi14 >= 70).length, fill: '#ff4d4d' },
  ]

  const adRatio = breadth
    ? ((breadth.strong_buy + breadth.buy) / Math.max(breadth.total, 1) * 100).toFixed(1)
    : '0'

  return (
    <div className="p-6 space-y-5">
      <h1 className="text-lg font-semibold text-white">Market Breadth</h1>

      {/* Summary Stats */}
      {breadth && (
        <div className="grid grid-cols-4 gap-3">
          <div className="bg-[#161b27] border border-[#2a3347] rounded-lg p-4 col-span-1">
            <p className="text-[10px] text-slate-500 mb-1">Advance/Decline</p>
            <p className={`text-2xl font-mono font-medium ${breadth.advance_decline >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {breadth.advance_decline >= 0 ? '+' : ''}{breadth.advance_decline}
            </p>
          </div>
          <div className="bg-[#161b27] border border-[#2a3347] rounded-lg p-4 col-span-1">
            <p className="text-[10px] text-slate-500 mb-1">Bull ratio</p>
            <p className="text-2xl font-mono font-medium text-blue-400">{adRatio}%</p>
          </div>
          <div className="bg-[#161b27] border border-[#2a3347] rounded-lg p-4 col-span-1">
            <p className="text-[10px] text-slate-500 mb-1">Strong signals</p>
            <p className="text-2xl font-mono font-medium text-white">{breadth.strong_buy + breadth.strong_sell}</p>
          </div>
          <div className="bg-[#161b27] border border-[#2a3347] rounded-lg p-4 col-span-1">
            <p className="text-[10px] text-slate-500 mb-1">Total F&O</p>
            <p className="text-2xl font-mono font-medium text-slate-300">{breadth.total}</p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-2 gap-4">
        {/* Pie Chart */}
        <div className="bg-[#161b27] border border-[#2a3347] rounded-lg p-4">
          <p className="text-xs text-slate-400 mb-4">Signal Distribution</p>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie data={pieData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} dataKey="value" paddingAngle={2}>
                {pieData.map((_, i) => <Cell key={i} fill={COLORS[i]} />)}
              </Pie>
              <Tooltip contentStyle={{ background: '#161b27', border: '1px solid #2a3347', fontSize: 11 }} />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex flex-wrap gap-2 justify-center mt-2">
            {pieData.map((d, i) => (
              <div key={d.name} className="flex items-center gap-1">
                <div className="w-2 h-2 rounded-full" style={{ background: COLORS[i] }} />
                <span className="text-[10px] text-slate-400">{d.name}: {d.value}</span>
              </div>
            ))}
          </div>
        </div>

        {/* RSI Distribution */}
        <div className="bg-[#161b27] border border-[#2a3347] rounded-lg p-4">
          <p className="text-xs text-slate-400 mb-4">RSI Distribution</p>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={rsiData}>
              <XAxis dataKey="range" tick={{ fill: '#64748b', fontSize: 10 }} tickLine={false} />
              <YAxis tick={{ fill: '#64748b', fontSize: 10 }} tickLine={false} />
              <Tooltip contentStyle={{ background: '#161b27', border: '1px solid #2a3347', fontSize: 11 }} />
              <Bar dataKey="count" radius={[3,3,0,0]}>
                {rsiData.map((d, i) => <Cell key={i} fill={d.fill} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
