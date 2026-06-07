import { useEffect, useRef } from 'react'
import { useScannerStore } from '../stores/scannerStore'

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null)
  const { setWsConnected, fetchSignals, fetchMarketData } = useScannerStore()

  useEffect(() => {
    const connect = () => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const ws = new WebSocket(`${protocol}//${window.location.host}/ws`)
      wsRef.current = ws

      ws.onopen = () => {
        setWsConnected(true)
        console.log('WS connected')
      }

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data)
          if (msg.type === 'scan_complete') {
            fetchSignals()
            fetchMarketData()
          } else if (msg.type === 'initial_state') {
            fetchSignals()
            fetchMarketData()
          }
          // heartbeat: ignore
        } catch {}
      }

      ws.onclose = () => {
        setWsConnected(false)
        // Reconnect after 3s
        setTimeout(connect, 3000)
      }

      ws.onerror = () => {
        ws.close()
      }
    }

    connect()

    const ping = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send('ping')
      }
    }, 25000)

    return () => {
      clearInterval(ping)
      wsRef.current?.close()
    }
  }, [])
}
