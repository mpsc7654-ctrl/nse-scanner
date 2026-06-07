import { NavLink } from 'react-router-dom'
import { useScannerStore } from '../../stores/scannerStore'
import {
  LayoutDashboard, Search, Star, BarChart2,
  TrendingUp, Wifi, WifiOff
} from 'lucide-react'

const nav = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/scanner', label: 'Scanner', icon: Search },
  { to: '/watchlist', label: 'Watchlist', icon: Star },
  { to: '/breadth', label: 'Market Breadth', icon: BarChart2 },
]

export default function Sidebar() {
  const { wsConnected, updatedAt } = useScannerStore()

  return (
    <aside className="w-56 min-h-screen bg-[#0d1220] border-r border-[#2a3347] flex flex-col flex-shrink-0">
      <div className="p-4 border-b border-[#2a3347]">
        <div className="flex items-center gap-2">
          <TrendingUp size={20} className="text-green-400" />
          <span className="font-semibold text-white text-sm">NSE F&amp;O Scanner</span>
        </div>
        <div className="flex items-center gap-1 mt-1">
          {wsConnected
            ? <><Wifi size={11} className="text-green-400" /><span className="text-[10px] text-green-400 ml-1">Live</span></>
            : <><WifiOff size={11} className="text-red-400" /><span className="text-[10px] text-red-400 ml-1">Polling</span></>
          }
        </div>
      </div>

      <nav className="flex-1 p-2 space-y-0.5">
        {nav.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${
                isActive
                  ? 'bg-blue-900/40 text-blue-400'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-[#1e2535]'
              }`
            }
          >
            <Icon size={16} />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="p-3 border-t border-[#2a3347]">
        {updatedAt && (
          <p className="text-[10px] text-slate-500">
            Updated {new Date(updatedAt).toLocaleTimeString()}
          </p>
        )}
        <p className="text-[10px] text-slate-600 mt-0.5">NSE 9:15 – 15:30 IST</p>
      </div>
    </aside>
  )
}
