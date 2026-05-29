import axios from 'axios'
import type { Team, TeamDetailed, TeamStatus, Frequency, GpsFrequencies, SiteStatusResponse, RecoveryPiece, AllRecoveryResponse } from '@/types'

const BASE_URL = import.meta.env.DEV
  ? 'http://localhost:8000/api'
  : 'https://tracker.faroutlaunch.org/api'

const api = axios.create({
  baseURL: BASE_URL,
  withCredentials: true,
})

let refreshPromise: Promise<void> | null = null

api.interceptors.response.use(
  r => r,
  async error => {
    const original = error.config
    const status = error.response?.status
    const url: string = original?.url ?? ''
    if (
      status === 401 &&
      !original?._retry &&
      !url.includes('/token/')
    ) {
      original._retry = true
      try {
        await (refreshPromise ??= (async () => {
          await axios.post(`${BASE_URL}/token/refresh/`, {}, { withCredentials: true })
        })().finally(() => { refreshPromise = null }))
        return api(original)
      } catch {
        throw error
      }
    }
    throw error
  }
)

export const getTeams = () => api.get<Team[]>('/team_tracking/teams').then(r => r.data)
export const postTeam = (data: Record<string, any>) => api.post('/team_tracking/teams', data).then(r => r.data)
export const patchTeam = (id: string, data: Record<string, any>) => api.patch(`/team_tracking/teams/${id}`, data).then(r => r.data)
export const getTeamsAbbreviated = () => api.get<Team[]>('/team_tracking/teams/abbreviated').then(r => r.data)
export const getTeam = (id: string) => api.get<TeamDetailed>(`/team_tracking/teams/${id}`).then(r => r.data)
export const getTeamStatuses = (id: string) => api.get<TeamStatus[]>(`/team_tracking/teams/${id}/status`).then(r => r.data)
export const getTeamRecovery = (id: string) => api.get<RecoveryPiece[]>(`/team_tracking/teams/${id}/recovery`).then(r => r.data)
export const getAllRecoveryPieces = () => api.get<AllRecoveryResponse>('/team_tracking/recovery').then(r => r.data)
export const getSiteStatus = () => api.get<SiteStatusResponse>('/team_tracking/site_status').then(r => r.data)
export const getFrequencies = () => api.get<Frequency[]>('/team_tracking/frequencies').then(r => r.data)
export const patchTeamFrequencies = (id: string, frequencies: GpsFrequencies) =>
  api.patch(`/team_tracking/teams/${id}/frequencies`, frequencies).then(r => r.data)

export const postLogin = (username: string, password: string) =>
  api.post('/token/', { username, password }).then(r => r.data)
export const postLogout = () => axios.post(`${BASE_URL}/logout/`, {}, { withCredentials: true })
export const getCurrentUser = () => api.get('/team_tracking/current-user').then(r => r.data)

export const postSiteStatus = (status: string) =>
  api.post('/team_tracking/site_status', { status }).then(r => r.data)
export const postTeamStatus = (teamId: string, status: string, padName?: string) =>
  api.post(`/team_tracking/teams/${teamId}/status`, { status, ...(padName ? { pad_name: padName } : {}) }).then(r => r.data)
export const postRecoveryPiece = (team: string, object_name: string, lat: number, lon: number) =>
  api.post(`/team_tracking/teams/${team}/recovery`, { object_name, lat, lon }).then(r => r.data)
export const deleteRecoveryPiece = (team: string, pieceId: number) =>
  api.delete(`/team_tracking/teams/${team}/recovery/${pieceId}`).then(r => r.data)
export const postRecoveryPath = (team: string, lat: number, lon: number) =>
  api.post(`/team_tracking/teams/${team}/recovery/path`, { lat, lon }).then(r => r.data)
