export const SiteStatus = {
  GREEN_FLAG: 'GREEN_FLAG',
  YELLOW_FLAG: 'YELLOW_FLAG',
  RED_FLAG: 'RED_FLAG',
} as const
export type SiteStatus = (typeof SiteStatus)[keyof typeof SiteStatus]

export interface User {
  id: number
  username: string
  email: string
  is_admin: boolean
  is_team_member: boolean
}

export interface Team {
  team_identifier: string
  name: string
  university: string
  category: string
  engine_type_display: string
  status: string
  pad_name: string | null
}

export interface TeamDetailed extends Team {
  fuel_oxidizer: string
  pad: string
  bunker: string
}

export interface TeamStatus {
  id: number
  status: string
  timestamp: string
  pad_name: string | null
}

export interface GpsFrequencies {
  avionics: string
  gse: string
  team_comms: string
}

export interface Frequency {
  name: string
  team_identifier: string
  gps_frequencies: GpsFrequencies
}

export interface SiteStatusResponse {
  status: string
  timestamp: string
}

export interface RecoveryPath {
  team_identifier: string
  name: string
  coords: { lon: number; lat: number; timestamp: string }[]
}

export interface AllRecoveryResponse {
  pieces: RecoveryPiece[]
  paths: RecoveryPath[]
}

export interface RecoveryPiece {
  id: number
  object_name: string
  lat: number
  lon: number
  team_name: string
  team_identifier: string
}

export interface RecoveryPathPoint {
  id: number
  lat: number
  lon: number
}

export interface ScheduleTeam {
  team_identifier: string
  name: string
  university: string
  category: string
  engine_type: string
  fill_to_fire: number
  hold_time: number
  salvo_time: number
  modifier_fraction?: number  // 0-6: 1, 1/2, 1/4, 1/8, 1/16, 1/32, 1/64 (higher positions are crossed off)
}

export interface ScheduleLane {
  id: string
  label: string
  short_label: string
  teams: ScheduleTeam[]
}

export interface SalvoScheduleResponse {
  lane_definitions: { id: string; label: string; short_label: string }[]
  lane_teams: Record<string, string[]>
  team_data: Record<string, Record<string, number>>
  salvo_timer_started: string | null
  teams: ScheduleTeam[]
}

export interface VoteBallot {
  id: number
  user: string
  choice: boolean
  cast_at: string
}

export interface Vote {
  id: number
  title: string
  created_by: string
  created_at: string
  expires_at: string
  duration_minutes: number
  is_active: boolean
  eligible_count: number
  ballots: VoteBallot[]
  yes_count: number
  no_count: number
  quorum_met: boolean
}
