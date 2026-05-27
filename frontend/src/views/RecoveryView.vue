<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import type { Feature, FeatureCollection } from 'geojson'
import mapboxgl from 'mapbox-gl'
import * as togeojson from '@mapbox/togeojson'
import { getMapboxToken } from '@/config'
import { getRecovery, getTeamsAbbreviated, getTeamRecovery, getTeam } from '@/api'
import type { Team, RecoveryPiece } from '@/types'
import 'mapbox-gl/dist/mapbox-gl.css'

const teams = ref<Team[]>([])
const allTeams = ref<Team[]>([])
const teamsWithPieces = ref<Set<string>>(new Set())
const loadingTeams = ref(true)
const teamsError = ref<string | null>(null)
const selectedTeamFilter = ref<string>('')

const filterableTeams = computed(() => {
  const ids = new Set([...teams.value.map(t => t.team_identifier), ...teamsWithPieces.value])
  return allTeams.value.filter(t => ids.has(t.team_identifier))
})

watch(selectedTeamFilter, () => Promise.all([updateRecoveryPieces(), updateTrajectories()]))

const mapContainer = ref<HTMLDivElement | null>(null)
let map: mapboxgl.Map | null = null
let resizeObserver: ResizeObserver | null = null
let pollInterval: ReturnType<typeof setInterval> | null = null

function midpoint(geometry: any): number[] {
  const coords: number[][] = []
  const collect = (g: any) => {
    if (g.type === 'LineString') coords.push(...g.coordinates)
    else if (g.type === 'MultiLineString') g.coordinates.forEach((c: number[][]) => coords.push(...c))
    else if (g.type === 'GeometryCollection') g.geometries.forEach(collect)
  }
  collect(geometry)
  if (!coords.length) return []
  return coords[Math.floor(coords.length / 2)]
}


async function fetchTeams() {
  try {
    ;[teams.value, allTeams.value] = await Promise.all([getRecovery(), getTeamsAbbreviated()])
    teamsError.value = null
  } catch {
    teamsError.value = 'Failed to load recovery teams'
  } finally {
    loadingTeams.value = false
  }
  await Promise.all([updateRecoveryPieces(), updateTrajectories()])
}

function visibleTeams() {
  return selectedTeamFilter.value
    ? teams.value.filter(t => t.team_identifier === selectedTeamFilter.value)
    : teams.value
}

async function updateTrajectories() {
  const trajSource = map?.getSource('trajectories') as mapboxgl.GeoJSONSource | undefined
  const dashSource = map?.getSource('trajectory-dashes') as mapboxgl.GeoJSONSource | undefined
  if (!trajSource || !dashSource) return

  const details = await Promise.all(
    visibleTeams().map(t => getTeam(t.team_identifier).catch(() => null))
  )

  const trajectoryFeatures: Feature[] = []
  const dashedFeatures: Feature[] = []

  for (const team of details) {
    if (!team) continue
    const coords: { lon: number; lat: number }[] = (team as any).recovery_coordinates?.coords ?? []
    if (!coords.length) continue

    const path = coords.map(c => [Number(c.lon), Number(c.lat)] as [number, number])
    trajectoryFeatures.push({
      type: 'Feature',
      geometry: { type: 'LineString', coordinates: path },
      properties: { name: team.name },
    })

    const last = path[path.length - 1]
    dashedFeatures.push({
      type: 'Feature',
      geometry: { type: 'Point', coordinates: last },
      properties: { label: `${team.name}\nCURRENT LOCATION` },
    })
  }

  trajSource.setData({ type: 'FeatureCollection', features: trajectoryFeatures })
  dashSource.setData({ type: 'FeatureCollection', features: dashedFeatures })
}

async function updateRecoveryPieces() {
  const source = map?.getSource('recovery-pieces') as mapboxgl.GeoJSONSource | undefined
  if (!source) return

  const allPiecesUnfiltered = (await Promise.all(
    allTeams.value.map(t => getTeamRecovery(t.team_identifier).then(pieces =>
      pieces.map(p => ({ ...p, teamName: t.name, teamId: t.team_identifier }))
    ).catch(() => []))
  )).flat()

  teamsWithPieces.value = new Set(allPiecesUnfiltered.map((p: any) => p.teamId))

  const allPieces = selectedTeamFilter.value
    ? allPiecesUnfiltered.filter((p: any) => p.teamId === selectedTeamFilter.value)
    : allPiecesUnfiltered

  source.setData({
    type: 'FeatureCollection',
    features: allPieces.map((p: RecoveryPiece & { teamName: string }) => ({
      type: 'Feature' as const,
      geometry: { type: 'Point' as const, coordinates: [p.lon, p.lat] },
      properties: { name: p.object_name, teamName: p.teamName },
    })),
  })
}

onMounted(async () => {
  await fetchTeams()
  pollInterval = setInterval(fetchTeams, 60_000)

  mapboxgl.accessToken = getMapboxToken()

  map = new mapboxgl.Map({
    container: mapContainer.value!,
    style: 'mapbox://styles/mapbox/satellite-streets-v12',
    center: [-117.80898, 35.34715],
    zoom: 14,
  })

  map.on('load', () => {
    fetch('/far_areas.kml')
      .then(r => r.text())
      .then(kmlText => {
        const kmlDoc = new DOMParser().parseFromString(kmlText, 'application/xml')
        const geojson = togeojson.kml(kmlDoc)

        const labelPoints = {
          type: 'FeatureCollection' as const,
          features: geojson.features.map((f: any) => ({
            type: 'Feature' as const,
            geometry: { type: 'Point' as const, coordinates: midpoint(f.geometry) },
            properties: {
              ...f.properties,
              name: (f.properties?.name ?? '').replace(/_/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase()),
            },
          })).filter((f: any) => f.geometry.coordinates.length),
        }

        map!.addSource('kml-source', { type: 'geojson', data: geojson as FeatureCollection })
        map!.addSource('kml-labels-source', { type: 'geojson', data: labelPoints })
        map!.addLayer({
          id: 'kml-layer',
          type: 'line',
          source: 'kml-source',
          paint: { 'line-color': '#FF0000', 'line-width': 2 },
        })
        map!.addLayer({
          id: 'kml-labels',
          type: 'symbol',
          source: 'kml-labels-source',
          layout: {
            'text-field': ['get', 'name'],
            'text-size': 14,
            'text-offset': [0, -1],
            'text-allow-overlap': true,
            'text-ignore-placement': true,
          },
          paint: {
            'text-color': '#FF0000',
            'text-halo-color': '#FFFFFF',
            'text-halo-width': 2,
          },
        })
      })
      .then(() => {
        const empty: FeatureCollection = { type: 'FeatureCollection', features: [] }
        map!.addSource('recovery-pieces', { type: 'geojson', data: empty })
        map!.addSource('trajectories', { type: 'geojson', data: empty })
        map!.addSource('trajectory-dashes', { type: 'geojson', data: empty })

        map!.addLayer({
          id: 'recovery-pieces-circles',
          type: 'circle',
          source: 'recovery-pieces',
          paint: { 'circle-radius': 6, 'circle-color': '#FFD700', 'circle-stroke-color': '#000', 'circle-stroke-width': 1 },
        })
        map!.addLayer({
          id: 'recovery-pieces-labels',
          type: 'symbol',
          source: 'recovery-pieces',
          layout: {
            'text-field': ['concat', ['get', 'name'], '\n', ['get', 'teamName']],
            'text-size': 12,
            'text-offset': [0, 1.2],
            'text-anchor': 'top',
            'text-allow-overlap': true,
            'text-ignore-placement': true,
          },
          paint: { 'text-color': '#FFD700', 'text-halo-color': '#000', 'text-halo-width': 1 },
        })
        map!.addLayer({
          id: 'trajectory-lines',
          type: 'line',
          source: 'trajectories',
          paint: { 'line-color': '#00BFFF', 'line-width': 2 },
        })
        map!.addLayer({
          id: 'trajectory-last-point',
          type: 'circle',
          source: 'trajectory-dashes',
          paint: { 'circle-radius': 7, 'circle-color': '#00FF00', 'circle-stroke-color': '#000', 'circle-stroke-width': 1 },
        })
        map!.addLayer({
          id: 'trajectory-last-point-label',
          type: 'symbol',
          source: 'trajectory-dashes',
          layout: {
            'text-field': ['get', 'label'],
            'text-size': 12,
            'text-offset': [0, 1.2],
            'text-anchor': 'top',
            'text-allow-overlap': true,
            'text-ignore-placement': true,
          },
          paint: { 'text-color': '#00FF00', 'text-halo-color': '#000', 'text-halo-width': 1 },
        })
      })
      .then(() => Promise.all([updateRecoveryPieces(), updateTrajectories()]))
      .catch(err => console.error('Error loading KML:', err))
  })

  resizeObserver = new ResizeObserver(() => map?.resize())
  resizeObserver.observe(mapContainer.value!)
})

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval)
  resizeObserver?.disconnect()
  map?.remove()
})
</script>

<template>
  <h1>Recovery</h1>
  <div class="recovery-layout">
    <div class="recovery-teams">
      <div v-if="loadingTeams">Loading...</div>
      <div v-else-if="teamsError">{{ teamsError }}</div>
      <template v-else>
        <div class="team-filter">
          <label>Filter map</label>
          <select v-model="selectedTeamFilter">
            <option value="">All Teams</option>
            <option v-for="t in filterableTeams" :key="t.team_identifier" :value="t.team_identifier">{{ t.name }}</option>
          </select>
        </div>
        <p v-if="teams.length === 0">No teams are presently out for recovery.</p>
        <div v-else class="table-wrapper">
          <table>
            <thead>
              <tr><th>Teams out for recovery</th></tr>
            </thead>
            <tbody>
              <tr v-for="team in teams" :key="team.team_identifier">
                <td>{{ team.name }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>
    </div>
    <div ref="mapContainer" class="recovery-map" />
  </div>
</template>

<style scoped>
.recovery-layout {
  display: flex;
  flex-direction: row;
  gap: 20px;
  align-items: stretch;
  height: calc(100vh - 16rem);
}

.recovery-teams {
  flex: 0 0 35%;
  overflow-y: auto;
}

.recovery-map {
  flex: 1;
  min-height: 0;
}

@media (max-width: 900px) {
  .recovery-layout {
    flex-direction: column;
    height: auto;
  }

  .recovery-teams {
    flex: 1 1 auto;
    max-height: 40vh;
  }

  .recovery-map {
    min-height: 50vh;
  }
}

.team-filter {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  color: var(--color-text);
}

.team-filter select {
  flex: 1;
  padding: 4px 8px;
  border-radius: 4px;
  border: 1px solid #888;
  background-color: transparent;
  color: var(--color-text);
}

.team-filter select option {
  background-color: white;
  color: var(--color-text-on-light);
}
</style>
