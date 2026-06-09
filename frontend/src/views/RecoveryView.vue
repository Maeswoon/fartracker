<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import type { Feature, FeatureCollection } from 'geojson'
import mapboxgl from 'mapbox-gl'
import { Threebox } from 'threebox-plugin'
import * as togeojson from '@mapbox/togeojson'
import { getMapboxToken, getTrajectoryWsUrl } from '@/config'
import { getTeamsAbbreviated, getAllRecoveryPieces } from '@/api'
import { useAuthStore } from '@/stores/auth'
import type { Team, RecoveryPiece, RecoveryPath } from '@/types'
import RecoveryPathManager from '@/components/RecoveryPathManager.vue'
import RecoveryPieceManager from '@/components/RecoveryPieceManager.vue'
import 'mapbox-gl/dist/mapbox-gl.css'

const auth = useAuthStore()
const isAdmin = computed(() => !!auth.user?.is_admin)

const allTeams = ref<Team[]>([])
const allPieces = ref<RecoveryPiece[]>([])
const paths = ref<RecoveryPath[]>([])
const loadingTeams = ref(true)
const teamsError = ref<string | null>(null)
const selectedTeamFilter = ref<string>('')
const showPieces = ref(true)
const showPaths = ref(false)
const showTrajectories = ref(false)

const trajectoryTeamIds = ref<Set<string>>(new Set())
const recoveryTeamIds = computed(() => {
  const ids = new Set<string>()
  if (showPieces.value) {
    for (const p of allPieces.value) ids.add(p.team_identifier)
  }
  if (showPaths.value) {
    for (const t of paths.value) ids.add(t.team_identifier)
  }
  if (showTrajectories.value) {
    for (const id of trajectoryTeamIds.value) ids.add(id)
  }
  return ids
})

const teams = computed(() =>
  allTeams.value.filter(t => t.status === 'Recovering')
)

const filterableTeams = computed(() => {
  const ids = new Set([
    ...teams.value.map(t => t.team_identifier),
    ...recoveryTeamIds.value,
  ])
  return allTeams.value.filter(t => ids.has(t.team_identifier))
})

watch(selectedTeamFilter, syncDisplay)

function syncDisplay() {
  if (!map) return
  updatePieceSource()
  updatePathSource()
  updateTrajectoryDisplay()
  updateLayerVisibility()
}

function updatePieceSource() {
  const source = map?.getSource('recovery-pieces') as mapboxgl.GeoJSONSource | undefined
  if (!source) return
  const filtered = selectedTeamFilter.value
    ? allPieces.value.filter(p => p.team_identifier === selectedTeamFilter.value)
    : allPieces.value
  source.setData({
    type: 'FeatureCollection',
    features: filtered.map(p => ({
      type: 'Feature' as const,
      geometry: { type: 'Point' as const, coordinates: [p.lon, p.lat] },
      properties: { name: p.object_name, teamName: p.team_name },
    })),
  })
}

function updatePathSource() {
  const pathSource = map?.getSource('paths') as mapboxgl.GeoJSONSource | undefined
  const dashSource = map?.getSource('path-dashes') as mapboxgl.GeoJSONSource | undefined
  const vertexSource = map?.getSource('path-vertices') as mapboxgl.GeoJSONSource | undefined
  if (!pathSource || !dashSource || !vertexSource) return

  const recoveringIds = new Set(teams.value.map(t => t.team_identifier))
  const filtered = selectedTeamFilter.value
    ? paths.value.filter(t => t.team_identifier === selectedTeamFilter.value && recoveringIds.has(t.team_identifier))
    : paths.value.filter(t => recoveringIds.has(t.team_identifier))

  const pathFeatures: Feature[] = []
  const dashedFeatures: Feature[] = []
  const vertexFeatures: Feature[] = []
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
    for (let i = 0; i < path.length - 1; i++) {
      vertexFeatures.push({
        type: 'Feature',
        geometry: { type: 'Point', coordinates: path[i] },
        properties: { label: `${team.name} (#${i + 1})` },
      })
    }
  }
  pathSource.setData({ type: 'FeatureCollection', features: pathFeatures })
  dashSource.setData({ type: 'FeatureCollection', features: dashedFeatures })
  vertexSource.setData({ type: 'FeatureCollection', features: vertexFeatures })
}

function updateTrajectoryDisplay() {
  if (!tb) return
  clearTrajectories()
  if (!showTrajectories.value) return
  const filtered = selectedTeamFilter.value
    ? allTrajectories.value.filter((t: any) => t.team_identifier === selectedTeamFilter.value)
    : allTrajectories.value
  filtered.forEach((t: any) => upsertTrajectory(t))
}

function updateLayerVisibility() {
  if (map?.getLayer('recovery-pieces-circles')) {
    const v = showPieces.value ? 'visible' : 'none'
    map!.setLayoutProperty('recovery-pieces-circles', 'visibility', v)
    map!.setLayoutProperty('recovery-pieces-labels', 'visibility', v)
  }
  if (map?.getLayer('path-lines')) {
    const v = showPaths.value ? 'visible' : 'none'
    map!.setLayoutProperty('path-lines', 'visibility', v)
    map!.setLayoutProperty('path-last-point', 'visibility', v)
    map!.setLayoutProperty('path-last-point-label', 'visibility', v)
    map!.setLayoutProperty('path-vertices-circles', 'visibility', v)
  }
}

const mapContainer = ref<HTMLDivElement | null>(null)
let map: mapboxgl.Map | null = null
let tb: InstanceType<typeof Threebox> | null = null
let resizeObserver: ResizeObserver | null = null
let pollInterval: ReturnType<typeof setInterval> | null = null
let ws: WebSocket | null = null
const trajectoryFeatures = ref<Feature[]>([])
const allTrajectories = ref<any[]>([])
const tbObjects: Map<number, any[]> = new Map()
const upsertTrajectory = (t: any) => {
  if (!tb) return
  if (!t.points || t.points.length < 2) return
  const objs: any[] = []
  const coords = t.points.map((p: number[]) => [p[1], p[0], p[2]])
  const line = tb.line({ geometry: coords, color: 0xff4500, width: 5, opacity: 0.9 })
  tb.add(line)
  objs.push(line)
  const last = t.points[t.points.length - 1]
  const lbl = tb.label({
    htmlElement: `<div class="trajectory-label">${t.team_name || ''}  ${last[2].toLocaleString()} ft</div>`,
    alwaysVisible: true,
  })
  lbl.setCoords([last[1], last[0], last[2] + 30])
  tb.add(lbl)
  objs.push(lbl)
  tbObjects.set(t.id, objs)
}
const clearTrajectories = () => {
  tbObjects.forEach((objs) => objs.forEach((o: any) => tb!.remove(o)))
  tbObjects.clear()
}
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
  syncDisplay()
}


onMounted(async () => {
  await fetchTeams()
  pollInterval = setInterval(fetchTeams, 15_000)

  mapboxgl.accessToken = getMapboxToken()

  map = new mapboxgl.Map({
    container: mapContainer.value!,
    style: 'mapbox://styles/mapbox/satellite-streets-v12',
    center: [-117.80898, 35.34715],
    zoom: 12.5,
  })

  tb = new Threebox(map, map.getCanvas().getContext('webgl')!, { defaultLights: true });
  (window as any).tb = tb

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
        map!.addSource('path-vertices', { type: 'geojson', data: empty })
        map!.addSource('trajectories', { type: 'geojson', data: empty })

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
        map!.addLayer({
          id: 'path-vertices-circles',
          type: 'circle',
          source: 'path-vertices',
          paint: { 'circle-radius': 4, 'circle-color': '#00BFFF', 'circle-stroke-color': '#000', 'circle-stroke-width': 1 },
        })
        map!.addLayer({
          id: 'trajectory-lines',
          type: 'custom',
          renderingMode: '3d',
          onAdd: function () {},
          render: function () {
            if (tb) tb.update()
          },
        })

        // Click-to-popup on recovery pieces
        map!.on('click', 'recovery-pieces-circles', (e) => {
          if (!e.features?.length) return
          const f = e.features[0]
          const coords = (f.geometry as any).coordinates as [number, number]
          new mapboxgl.Popup()
            .setLngLat(coords)
            .setHTML(`<strong>${f.properties?.name || ''}</strong><br>${coords[1].toFixed(5)}, ${coords[0].toFixed(5)}`)
            .addTo(map!)
        })
        map!.on('mouseenter', 'recovery-pieces-circles', () => { map!.getCanvas().style.cursor = 'pointer' })
        map!.on('mouseleave', 'recovery-pieces-circles', () => { map!.getCanvas().style.cursor = '' })

        map!.on('click', 'path-last-point', (e) => {
          if (!e.features?.length) return
          const f = e.features[0]
          const coords = (f.geometry as any).coordinates as [number, number]
          new mapboxgl.Popup()
            .setLngLat(coords)
            .setHTML(`<strong>${f.properties?.label || ''}</strong><br>${coords[1].toFixed(5)}, ${coords[0].toFixed(5)}`)
            .addTo(map!)
        })
        map!.on('mouseenter', 'path-last-point', () => { map!.getCanvas().style.cursor = 'pointer' })
        map!.on('mouseleave', 'path-last-point', () => { map!.getCanvas().style.cursor = '' })

        map!.on('click', 'path-vertices-circles', (e) => {
          if (!e.features?.length) return
          const f = e.features[0]
          const coords = (f.geometry as any).coordinates as [number, number]
          new mapboxgl.Popup()
            .setLngLat(coords)
            .setHTML(`<strong>${f.properties?.label || ''}</strong><br>${coords[1].toFixed(5)}, ${coords[0].toFixed(5)}`)
            .addTo(map!)
        })
        map!.on('mouseenter', 'path-vertices-circles', () => { map!.getCanvas().style.cursor = 'pointer' })
        map!.on('mouseleave', 'path-vertices-circles', () => { map!.getCanvas().style.cursor = '' })
      })
      .then(syncDisplay)
      .catch(err => console.error('Error loading KML:', err))
  })

  watch(showTrajectories, (val) => {
    map?.easeTo({ pitch: val ? 60 : 0, zoom: val ? 9.5 : 12.5, center: [-117.80898, 35.34715] })
    if (val) {
      ws = new WebSocket(getTrajectoryWsUrl())
      ws.onmessage = (event) => {
        const msg = JSON.parse(event.data)
        const source = map?.getSource('trajectories') as mapboxgl.GeoJSONSource | undefined
        if (!source) return
        const makeFeature = (t: any) => ({
          type: 'Feature' as const,
          geometry: { type: 'LineString' as const, coordinates: (t.points || []).map((p: number[]) => [p[1], p[0]]) },
          properties: { id: t.id, name: t.team_name, team_identifier: t.team_identifier, altitudes: (t.points || []).map((p: number[]) => p[2]) },
        })
        if (msg.type === 'initial') {
          trajectoryFeatures.value = msg.trajectories.map(makeFeature)
        } else {
          const idx = trajectoryFeatures.value.findIndex((f: any) => f.properties?.id === msg.trajectory?.id)
          const feat = makeFeature(msg.trajectory)
          const current = trajectoryFeatures.value
          trajectoryFeatures.value = idx >= 0
            ? [...current.slice(0, idx), feat, ...current.slice(idx + 1)]
            : [...current, feat]
        }
        source.setData({ type: 'FeatureCollection', features: trajectoryFeatures.value })
        if (msg.type === 'initial') {
          allTrajectories.value = msg.trajectories
          trajectoryTeamIds.value = new Set<string>(msg.trajectories.map((t: any) => t.team_identifier as string))
        } else {
          const idx = allTrajectories.value.findIndex((t: any) => t.id === msg.trajectory.id)
          if (idx >= 0) allTrajectories.value[idx] = msg.trajectory
          else allTrajectories.value.push(msg.trajectory)
          trajectoryTeamIds.value = new Set([...trajectoryTeamIds.value, msg.trajectory.team_identifier])
        }
        syncDisplay()
      }
    } else {
      ws?.close()
      ws = null
      syncDisplay()
    }
  })

  watch(showPieces, syncDisplay)
  watch(showPaths, syncDisplay)

  resizeObserver = new ResizeObserver(() => map?.resize())
  resizeObserver.observe(mapContainer.value!)
})

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval)
  ws?.close()
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
          <label>Filter teams</label>
          <select v-model="selectedTeamFilter">
            <option value="">All Teams</option>
            <option v-for="t in filterableTeams" :key="t.team_identifier" :value="t.team_identifier">{{ t.name }}</option>
          </select>
        </div>
        <div class="display-options">
          <h4>Display</h4>
          <label class="toggle-row">
            <span>Pieces</span>
            <input v-model="showPieces" type="checkbox" class="toggle-input" />
            <span class="toggle-slider"></span>
          </label>
          <label class="toggle-row">
            <span>Paths</span>
            <input v-model="showPaths" type="checkbox" class="toggle-input" />
            <span class="toggle-slider"></span>
          </label>
          <label class="toggle-row">
            <span>Flight trajectories</span>
            <input v-model="showTrajectories" type="checkbox" class="toggle-input" />
            <span class="toggle-slider"></span>
          </label>
        </div>
        <template v-if="isAdmin">
          <RecoveryPathManager :teams="allTeams" @updated="fetchTeams" />
          <RecoveryPieceManager :teams="allTeams" @updated="fetchTeams" />
        </template>
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
  flex: 0 0 25%;
  overflow-y: auto;
}

.recovery-map {
  flex: 1;
  min-height: 0;
  border-radius: 8px;
  overflow: hidden;
}

.recovery-teams :deep(.form-card--wide) {
  max-width: none;
  margin-bottom: 16px;
}
.recovery-teams :deep(.form-card input),
.recovery-teams :deep(.form-card select),
.recovery-teams :deep(.form-card textarea) {
  margin-bottom: 4px;
  padding: 4px 6px;
  font-size: 0.82rem;
}
.recovery-teams :deep(.form-card label) {
  margin-bottom: 2px;
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
  background-color: var(--color-input-bg);
  color: var(--color-text);
}

.display-options {
  margin-bottom: 24px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 12px;
}

.toggle-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  cursor: pointer;
  color: var(--color-text);
}

.toggle-input {
  display: none;
}

.toggle-slider {
  position: relative;
  width: 44px;
  height: 24px;
  flex-shrink: 0;
  background: var(--color-toggle-off);
  border-radius: 12px;
  transition: background 0.2s;
}

.toggle-slider::after {
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  width: 20px;
  height: 20px;
  background: white;
  border-radius: 50%;
  transition: transform 0.2s;
}

.toggle-input:checked + .toggle-slider {
  background: var(--color-accent-red);
}

.toggle-input:checked + .toggle-slider::after {
  transform: translateX(20px);
}
</style>

<style>
.mapboxgl-popup-content {
  background: var(--color-surface) !important;
  color: var(--color-text) !important;
  border-radius: 6px;
  padding: 8px 12px;
  font-size: 0.85rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.3);
}
.mapboxgl-popup-tip { border-top-color: var(--color-surface) !important; }
.mapboxgl-popup-close-button { color: var(--color-text-muted); }
</style>
