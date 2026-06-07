let mapboxToken: string | null = null

export async function loadConfig(): Promise<void> {
  if (import.meta.env.DEV) {
    mapboxToken = import.meta.env.VITE_MAPBOX_TOKEN ?? null
    return
  }
  const res = await fetch('/config.json', { cache: 'no-store' })
  if (!res.ok) throw new Error(`Failed to load /config.json: ${res.status}`)
  const cfg = await res.json()
  mapboxToken = cfg.mapboxToken ?? null
}

export function getMapboxToken(): string {
  if (!mapboxToken) {
    throw new Error('Mapbox token is not configured. Set VITE_MAPBOX_TOKEN (dev) or dist/config.json mapboxToken (prod).')
  }
  return mapboxToken
}

export function getTrajectoryWsUrl(): string {
  return import.meta.env.DEV
    ? 'ws://localhost:8000/ws/trajectories/'
    : 'wss://tracker.faroutlaunch.org/ws/trajectories/'
}

export function getScheduleWsUrl(): string {
  return import.meta.env.DEV
    ? 'ws://localhost:8000/ws/'
    : 'wss://tracker.faroutlaunch.org/ws/'
}
