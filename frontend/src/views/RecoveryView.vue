<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import type { Feature, FeatureCollection } from 'geojson'
import mapboxgl from 'mapbox-gl'
import * as togeojson from '@mapbox/togeojson'
import { getMapboxToken } from '@/config'
import { getTeamsAbbreviated, getAllRecoveryPieces } from '@/api'
import type { Team, RecoveryPiece, RecoveryPath } from '@/types'
import 'mapbox-gl/dist/mapbox-gl.css'

const allTeams = ref<Team[]>([])
const allPieces = ref<RecoveryPiece[]>([])
const paths = ref<RecoveryPath[]>([])
const loadingTeams = ref(true)
const teamsError = ref<string | null>(null)
const selectedTeamFilter = ref<string>('')

const recoveryTeamIds = computed(() => {
  const ids = new Set<string>()
  for (const p of allPieces.value) ids.add((p as any).team_identifier)
  for (const t of paths.value) ids.add(t.team_identifier)
  return ids
})

const teams = computed(() =>
  allTeams.value.filter(t => t.status === 'IR')
)

const filterableTeams = computed(() => {
  const ids = new Set([
    ...teams.value.map(t => t.team_identifier),
    ...recoveryTeamIds.value,
  ])
  return allTeams.value.filter(t => ids.has(t.team_identifier))
})

watch(selectedTeamFilter, () => Promise.all([updateRecoveryPieces(), updatePaths()]))

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
    const [allTeamsList, recoveryData] = await Promise.all([
      getTeamsAbbreviated(),
      getAllRecoveryPieces().catch(() => ({ pieces: [], paths: [] })),
    ])
    allTeams.value = allTeamsList
    allPieces.value = recoveryData.pieces
    paths.value = recoveryData.paths
    teamsError.value = null
  } catch {
    teamsError.value = 'Failed to load recovery teams'
  } finally {
    loadingTeams.value = false
  }
  await updateRecoveryPieces()
  await updatePaths()
}

function updatePaths() {
  const pathSource = map?.getSource('paths') as mapboxgl.GeoJSONSource | undefined
  const dashSource = map?.getSource('path-dashes') as mapboxgl.GeoJSONSource | undefined
  if (!pathSource || !dashSource) return

  const recoveringIds = new Set(teams.value.map(t => t.team_identifier))
  const filtered = selectedTeamFilter.value
    ? paths.value.filter(t => t.team_identifier === selectedTeamFilter.value && recoveringIds.has(t.team_identifier))
    : paths.value.filter(t => recoveringIds.has(t.team_identifier))

  const pathFeatures: Feature[] = []
  const dashedFeatures: Feature[] = []

  for (const team of filtered) {
    if (!team.coords.length) continue
    const path = team.coords.map(c => [Number(c.lon), Number(c.lat)] as [number, number])
    pathFeatures.push({
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

  pathSource.setData({ type: 'FeatureCollection', features: pathFeatures })
  dashSource.setData({ type: 'FeatureCollection', features: dashedFeatures })
}

function updateRecoveryPieces() {
  const source = map?.getSource('recovery-pieces') as mapboxgl.GeoJSONSource | undefined
  if (!source) return

  const filteredPieces = selectedTeamFilter.value
    ? allPieces.value.filter((p: any) => p.team_identifier === selectedTeamFilter.value)
    : allPieces.value

  source.setData({
    type: 'FeatureCollection',
    features: filteredPieces.map((p: any) => ({
      type: 'Feature' as const,
      geometry: { type: 'Point' as const, coordinates: [p.lon, p.lat] },
      properties: { name: p.object_name, teamName: p.team_name },
    })),
  })
}

onMounted(async () => {
  await fetchTeams()
  pollInterval = setInterval(fetchTeams, 15_000)

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
        map!.addSource('paths', { type: 'geojson', data: empty })
        map!.addSource('path-dashes', { type: 'geojson', data: empty })

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
          id: 'path-lines',
          type: 'line',
          source: 'paths',
          paint: { 'line-color': '#00BFFF', 'line-width': 2 },
        })
        map!.addLayer({
          id: 'path-last-point',
          type: 'circle',
          source: 'path-dashes',
          paint: { 'circle-radius': 7, 'circle-color': '#00FF00', 'circle-stroke-color': '#000', 'circle-stroke-width': 1 },
        })
        map!.addLayer({
          id: 'path-last-point-label',
          type: 'symbol',
          source: 'path-dashes',
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
      .then(() => Promise.all([updateRecoveryPieces(), updatePaths()]))
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
