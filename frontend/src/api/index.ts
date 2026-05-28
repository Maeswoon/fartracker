import axios from 'axios'
import type { Team, TeamDetailed, TeamStatus, Frequency, GpsFrequencies, SiteStatusResponse, RecoveryPiece } from '@/types'

const BASE_URL = import.meta.env.DEV
  ? 'http://localhost:8000/api'
  : 'https://tracker.faroutlaunch.org/api'

const api = axios.create({
  baseURL: BASE_URL,
})

const authHeaders = () => {
  const token = localStorage.getItem('access')
  return token ? { Authorization: `Bearer ${token}` } : {}
}
const authConfig = () => ({ headers: authHeaders() })

api.interceptors.request.use(config => {
  const token = localStorage.getItem('access')
  if (token && !config.headers?.Authorization) {
    config.headers = config.headers ?? {}
    ;(config.headers as any).Authorization = `Bearer ${token}`
  }
  return config
})

let refreshPromise: Promise<string> | null = null

const refreshAccessToken = async (): Promise<string> => {
  const refresh = localStorage.getItem('refresh')
  if (!refresh) throw new Error('no refresh token')
  const { data } = await axios.post<{ access: string }>(`${BASE_URL}/token/refresh/`, { refresh })
  localStorage.setItem('access', data.access)
  return data.access
}

api.interceptors.response.use(
  r => r,
  async error => {
    const original = error.config
    const status = error.response?.status
    const url: string = original?.url ?? ''
    if (
      status === 401 &&
      !original?._retry &&
      !url.includes('/token/') &&
      localStorage.getItem('refresh')
    ) {
      original._retry = true
      try {
        const access = await (refreshPromise ??= refreshAccessToken().finally(() => { refreshPromise = null }))
        original.headers = original.headers ?? {}
        original.headers.Authorization = `Bearer ${access}`
        return api(original)
      } catch (e) {
        localStorage.removeItem('access')
        localStorage.removeItem('refresh')
        throw e
      }
    }
    throw error
  }
)

export const getTeams = () => api.get<Team[]>('/team_tracking/teams').then(r => r.data)
export const postTeam = (data: Record<string, any>) => api.post('/team_tracking/teams', data, authConfig()).then(r => r.data)
export const patchTeam = (id: string, data: Record<string, any>) => api.patch(`/team_tracking/teams/${id}`, data, authConfig()).then(r => r.data)
export const getTeamsAbbreviated = () => api.get<Team[]>('/team_tracking/teams/abbreviated').then(r => r.data)
export const getTeam = (id: string) => api.get<TeamDetailed>(`/team_tracking/teams/${id}`).then(r => r.data)
export const getTeamStatuses = (id: string) => api.get<TeamStatus[]>(`/team_tracking/teams/${id}/status`).then(r => r.data)
export const getTeamRecovery = (id: string) => api.get<RecoveryPiece[]>(`/team_tracking/teams/${id}/recovery`).then(r => r.data)
export const getSiteStatus = () => api.get<SiteStatusResponse>('/team_tracking/site_status').then(r => r.data)
export const getFrequencies = () => api.get<Frequency[]>('/team_tracking/frequencies').then(r => r.data)
export const patchTeamFrequencies = (id: string, frequencies: GpsFrequencies) =>
  api.patch(`/team_tracking/teams/${id}/frequencies`, frequencies, authConfig()).then(r => r.data)
export const getRecovery = () => api.get<Team[]>('/team_tracking/recovery').then(r => r.data)

export const postLogin = (username: string, password: string) =>
  api.post<{ access: string; refresh: string }>('/token/', { username, password }).then(r => r.data)
export const getCurrentUser = () => api.get('/team_tracking/current-user', authConfig()).then(r => r.data)

export const postSiteStatus = (status: string) =>
  api.post('/team_tracking/site_status', { status }, authConfig()).then(r => r.data)
export const postTeamStatus = (teamId: string, status: string, padName?: string) =>
  api.post(`/team_tracking/teams/${teamId}/status`, { status, ...(padName ? { pad_name: padName } : {}) }, authConfig()).then(r => r.data)
export const postRecoveryPiece = (team: string, object_name: string, lat: number, lon: number) =>
  api.post(`/team_tracking/teams/${team}/recovery`, { object_name, lat, lon }, authConfig()).then(r => r.data)
export const postRecoveryTrajectory = (team: string, lat: number, lon: number) =>
  api.post(`/team_tracking/teams/${team}/recovery/trajectory`, { lat, lon }, authConfig()).then(r => r.data)
