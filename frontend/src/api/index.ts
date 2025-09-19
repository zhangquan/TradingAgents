import axios from 'axios'

// In production, use relative URL since frontend is served by the same backend
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || (
  import.meta.env.MODE === 'production' ? '' : 'http://localhost:8000'
)

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add request interceptor for auth and language
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  
  // Add browser language preference to headers
  const browserLanguage = navigator.language || navigator.languages?.[0] || 'en-US'
  config.headers['Accept-Language'] = browserLanguage
  
  return config
})

// WebSocket connection for system updates (optional)
export function createWebSocket(): WebSocket {
  const wsUrl = API_BASE_URL.replace('http', 'ws') + `/ws`
  return new WebSocket(wsUrl)
}

// Health check
export async function healthCheck() {
  const response = await api.get('/health')
  return response.data
}

// Export the base URL for module use
export { API_BASE_URL }
