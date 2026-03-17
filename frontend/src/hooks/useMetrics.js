import { useEffect, useRef } from 'react'
import { createMetricsSocket } from '../services/websocket'

export function useMetrics({ enabled, onFrame, onSocketState }) {
  const socketRef = useRef(null)

  useEffect(() => {
    if (!enabled) return undefined

    const socket = createMetricsSocket({
      onOpen: () => onSocketState?.('connected'),
      onClose: () => onSocketState?.('disconnected'),
      onError: () => onSocketState?.('error'),
      onMessage: (payload) => onFrame?.(payload),
    })

    socketRef.current = socket

    return () => {
      if (socketRef.current && socketRef.current.readyState <= 1) {
        socketRef.current.close()
      }
      socketRef.current = null
    }
  }, [enabled, onFrame, onSocketState])
}
