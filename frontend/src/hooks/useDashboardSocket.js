import { useEffect, useRef } from 'react'

const WS_BASE_URL =
  window.__ENV__?.WS_BASE_URL || import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000'

export function useDashboardSocket(token, onMessage) {
  const onMessageRef = useRef(onMessage)
  onMessageRef.current = onMessage

  useEffect(() => {
    if (!token) return undefined
    let socket
    let reconnectTimer
    let closedByClient = false
    let attempt = 0

    function connect() {
      socket = new WebSocket(`${WS_BASE_URL}/ws/dashboard?token=${encodeURIComponent(token)}`)

      socket.onmessage = (event) => {
        try {
          const parsed = JSON.parse(event.data)
          onMessageRef.current?.(parsed)
        } catch (e) {
        }
      }

      socket.onclose = () => {
        if (closedByClient) return
        attempt += 1
        const delay = Math.min(1000 * 2 ** attempt, 15000)
        reconnectTimer = setTimeout(connect, delay)
      }

      socket.onerror = () => {
        socket.close()
      }

      socket.onopen = () => {
        attempt = 0
      }
    }

    connect()

    return () => {
      closedByClient = true
      clearTimeout(reconnectTimer)
      socket?.close()
    }
  }, [token])
}
