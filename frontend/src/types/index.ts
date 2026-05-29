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

export interface RecoveryTrajectory {
  team_identifier: string
  name: string
  coords: { lon: number; lat: number; timestamp: string }[]
}

export interface AllRecoveryResponse {
  pieces: RecoveryPiece[]
  trajectories: RecoveryTrajectory[]
}

export interface RecoveryPiece {
  id: number
  object_name: string
  lat: number
  lon: number
  team_name?: string
  team_identifier?: string
}

export interface RecoveryTrajectoryPoint {
  id: number
  lat: number
  lon: number
}
