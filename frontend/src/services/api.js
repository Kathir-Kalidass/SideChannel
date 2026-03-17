import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 8000,
})

export async function startSimulation(config) {
  const { data } = await api.post('/simulation/start', config)
  return data
}

export async function stopSimulation() {
  const { data } = await api.post('/simulation/stop')
  return data
}

export async function resetSimulation() {
  const { data } = await api.post('/simulation/reset')
  return data
}

export async function getSimulationStatus() {
  const { data } = await api.get('/simulation/status')
  return data
}

export async function getCurrentMetrics() {
  const { data } = await api.get('/metrics/current')
  return data
}

export async function getMetricsHistory(limit = 60) {
  const { data } = await api.get('/metrics/history', { params: { limit } })
  return data
}

export async function startAttack() {
  const { data } = await api.post('/attack/start')
  return data
}

export async function getAttackStatus() {
  const { data } = await api.get('/attack/status')
  return data
}

export async function getAttackLog() {
  const { data } = await api.get('/attack/log')
  return data
}

export async function getAIPrediction() {
  const { data } = await api.get('/ai/prediction')
  return data
}

export async function trainAI() {
  const { data } = await api.post('/ai/train')
  return data
}

export async function getDefenseStatus() {
  const { data } = await api.get('/defense/status')
  return data
}

export async function activateDefense(technique = 'masking') {
  const { data } = await api.post('/defense/activate', { technique })
  return data
}

export async function disableDefense() {
  const { data } = await api.post('/defense/disable')
  return data
}

export async function exportDataset() {
  const { data } = await api.get('/dataset/export', { responseType: 'blob' })
  return data
}

export async function listPaymentUsers() {
  const { data } = await api.get('/payments/users')
  return data
}

export async function loginPaymentUser(username, password) {
  const { data } = await api.post('/payments/login', { username, password })
  return data.user
}

export async function getPaymentHistory(limit = 100) {
  const { data } = await api.get('/payments/history', { params: { limit } })
  return data
}

export async function savePaymentHistory(payload) {
  const { data } = await api.post('/payments/history', payload)
  return data
}

export async function getAdaptivePolicy(senderUserId, receiverUserId) {
  const { data } = await api.get('/payments/adaptive-policy', {
    params: {
      sender_user_id: senderUserId,
      receiver_user_id: receiverUserId,
    },
  })
  return data
}

export default api
