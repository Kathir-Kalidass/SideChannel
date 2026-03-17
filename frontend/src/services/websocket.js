const WS_PATH = '/api/v1/ws/metrics'

function buildUrl() {
  const custom = import.meta.env.VITE_WS_URL
  if (custom) return custom

  const apiBase = import.meta.env.VITE_API_BASE_URL
  if (apiBase && apiBase.startsWith('http')) {
    const apiUrl = new URL(apiBase)
    const wsProtocol = apiUrl.protocol === 'https:' ? 'wss:' : 'ws:'
    return `${wsProtocol}//${apiUrl.host}${WS_PATH}`
  }

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = import.meta.env.VITE_WS_HOST || window.location.host
  return `${protocol}//${host}${WS_PATH}`
}

export function createMetricsSocket({ onMessage, onOpen, onClose, onError }) {
  const socket = new WebSocket(buildUrl())

  socket.onopen = () => {
    if (onOpen) onOpen()
  }

  socket.onmessage = (event) => {
    try {
      const payload = JSON.parse(event.data)
      if (onMessage) onMessage(payload)
    } catch {
      if (onError) onError(new Error('Invalid WebSocket payload'))
    }
  }

  socket.onerror = () => {
    if (onError) onError(new Error('WebSocket connection error'))
  }

  socket.onclose = () => {
    if (onClose) onClose()
  }

  return socket
}
