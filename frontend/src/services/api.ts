import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000/api',
})

api.interceptors.response.use((response) => response, (error) => {
  if (error.response?.status === 401 && localStorage.getItem('maternasense_token')) {
    localStorage.removeItem('maternasense_token')
    window.dispatchEvent(new Event('maternasense:unauthorized'))
  }
  return Promise.reject(error)
})

export type DashboardStats = {
  total_mothers: number
  active_pregnancies: number
  high_risk_cases: number
  moderate_risk_cases: number
  low_risk_cases: number
  newborns_monitored: number
}

export type AlertRecord = {
  id: number
  mother_id: number
  risk_level: string
  risk_score: number
  status: string
  created_at: string
}

export type MotherRecord = {
  id: number
  mother_code: string
  name: string
  age?: number | null
  source_type?: string
  antenatal_visit_count?: number
  current_prediction: { risk_score: number; risk_level: string } | null
}

export type AuthUser = { id: number; name: string; email: string; role: string }

export async function login(email: string, password: string) {
  const response = await api.post<{ access_token: string; user: AuthUser }>('/auth/login', { email, password })
  localStorage.setItem('maternasense_token', response.data.access_token)
  return response.data.user
}

export function logout() { localStorage.removeItem('maternasense_token') }
export function hasSession() { return Boolean(localStorage.getItem('maternasense_token')) }

export async function validateSession() {
  await api.get('/auth/me', await authConfig())
}

export async function loadModelPerformance() {
  const response = await api.get('/model/performance', await authConfig())
  return response.data
}

export async function loadDashboard() {
  const config = await authConfig()
  const [stats, alerts, mothers] = await Promise.all([
    api.get<DashboardStats>('/dashboard/stats', config),
    api.get<{ items: AlertRecord[] }>('/alerts', config),
    api.get<{ items: MotherRecord[] }>('/mothers', config),
  ])
  const featured = mothers.data.items.find((mother) => mother.mother_code === 'M003')
  const history = featured ? await api.get<{ items: PredictionRecord[] }>(`/mothers/${featured.id}/predictions`, config) : null
  return { stats: stats.data, alerts: alerts.data.items, mothers: mothers.data.items, featuredPredictions: history?.data.items || [] }
}

export type TimelineEvent = {
  type: string
  date: string
  data: { id: number; gestational_age?: number; systolic_bp?: number; diastolic_bp?: number; blood_sugar?: number; hemoglobin?: number; delivery_mode?: string; delivery_place?: string; newborn_code?: string; birth_weight?: number; sex?: string; nicu_required?: boolean; days_after_delivery?: number; newborn_weight?: number; feeding_status?: string; newborn_condition?: string }
  prediction: { risk_score: number; risk_level: string; factors: { feature: string; contribution: number; direction: string }[] } | null
}

async function authConfig() {
  const token = localStorage.getItem('maternasense_token')
  if (!token) throw new Error('Authentication required')
  return { headers: { Authorization: `Bearer ${token}` } }
}

export async function loadMothers(search = '') {
  const response = await api.get<{ items: MotherRecord[] }>('/mothers', { ...(await authConfig()), params: { search } })
  return response.data.items
}

export async function loadMotherTimeline(id: number) {
  const response = await api.get<{ mother: MotherRecord; events: TimelineEvent[] }>(`/mothers/${id}/timeline`, await authConfig())
  return response.data
}

export async function saveAntenatalVisit(id: number, values: Record<string, unknown>) {
  const response = await api.post(`/mothers/${id}/antenatal-visits`, values, await authConfig())
  return response.data as { prediction: { risk_score: number; risk_level: string }; message: string }
}

export async function saveDelivery(id: number, values: Record<string, unknown>) {
  const response = await api.post(`/mothers/${id}/delivery`, values, await authConfig())
  return response.data as { message: string }
}

export async function saveNewborn(id: number, values: Record<string, unknown>) {
  const response = await api.post(`/mothers/${id}/newborn`, values, await authConfig())
  return response.data as { newborn_id: number; message: string }
}

export async function savePostnatalVisit(id: number, values: Record<string, unknown>) {
  const response = await api.post(`/mothers/${id}/postnatal-visits`, values, await authConfig())
  return response.data as { message: string }
}

export type PredictionRecord = {
  id: number
  risk_score: number
  risk_level: string
  model_name: string
  is_demo_prediction: boolean
  timestamp: string
  factors: { feature: string; value: unknown; contribution: number; direction: string }[]
}

export async function loadPredictions(id: number) {
  const response = await api.get<{ items: PredictionRecord[] }>(`/mothers/${id}/predictions`, await authConfig())
  return response.data.items
}

export async function loadAlerts() {
  const response = await api.get<{ items: AlertRecord[] }>('/alerts', await authConfig())
  return response.data.items
}

export async function updateAlert(id: number, status: 'NEW' | 'REVIEWED' | 'RESOLVED') {
  const response = await api.put<{ id: number; status: string }>(`/alerts/${id}/status`, { status }, await authConfig())
  return response.data
}

export async function createMother(values: { mother_code: string; name: string; age?: number; blood_group?: string }) {
  const response = await api.post<MotherRecord>('/mothers', values, await authConfig())
  return response.data
}
