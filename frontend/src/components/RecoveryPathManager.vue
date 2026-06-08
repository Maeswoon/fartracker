<script setup lang="ts">
import { ref, watch } from 'vue'
import { getTeamRecoveryPath, putTeamRecoveryPath, deleteRecoveryPathPoint, postRecoveryPath } from '@/api'
import type { Team } from '@/types'
import TeamSelect from '@/components/TeamSelect.vue'
import CoordinateInput from '@/components/CoordinateInput.vue'

const props = defineProps<{ teams: Team[] }>()
const emit = defineEmits<{ updated: [] }>()

interface PathPoint { lat: number; lon: number; timestamp?: string }

function fmtTs(ts?: string) {
  if (!ts) return '—'
  const d = new Date(ts)
  return d.toLocaleTimeString()
}

const team = ref('')
const points = ref<PathPoint[]>([])
const loading = ref(false)
const message = ref('')
const errorMsg = ref('')
const newLat = ref(0)
const newLon = ref(0)

async function loadPath() {
  if (!team.value) { points.value = []; return }
  loading.value = true
  try {
    const data = await getTeamRecoveryPath(team.value)
    points.value = data.coords || []
    message.value = ''
    errorMsg.value = ''
  } catch {
    errorMsg.value = 'Failed to load path.'
  } finally {
    loading.value = false
  }
}

watch(team, loadPath)

async function savePath() {
  loading.value = true
  message.value = ''
  errorMsg.value = ''
  try {
    const coords = points.value.map(p => ({ lat: p.lat, lon: p.lon, timestamp: p.timestamp }))
    await putTeamRecoveryPath(team.value, coords)
    message.value = 'Saved.'
    emit('updated')
  } catch {
    errorMsg.value = 'Failed to save.'
  } finally {
    loading.value = false
  }
}

async function deletePoint(index: number) {
  if (!window.confirm('Delete this point?')) return
  loading.value = true
  errorMsg.value = ''
  try {
    await deleteRecoveryPathPoint(team.value, index)
    points.value.splice(index, 1)
    message.value = 'Point deleted.'
    emit('updated')
  } catch {
    errorMsg.value = 'Failed to delete.'
  } finally {
    loading.value = false
  }
}

async function addPoint() {
  if (!team.value) return
  loading.value = true
  errorMsg.value = ''
  try {
    await postRecoveryPath(team.value, newLat.value, newLon.value)
    newLat.value = 0
    newLon.value = 0
    await loadPath()
    message.value = 'Point added.'
    emit('updated')
  } catch {
    errorMsg.value = 'Failed to add point.'
  } finally {
    loading.value = false
  }
}

defineExpose({ refresh: loadPath })
</script>

<template>
  <div class="form-card form-card--wide">
    <h3>Recovery Path Points</h3>
    <p v-if="message" class="success">{{ message }}</p>
    <p v-if="errorMsg" class="error">{{ errorMsg }}</p>

    <label>Team</label>
    <TeamSelect v-model="team" :teams="props.teams" />

    <div v-if="team" class="add-point">
      <label>Add Point</label>
      <div class="add-row">
        <CoordinateInput v-model="newLat" axis="lat" compact />
        <CoordinateInput v-model="newLon" axis="lon" compact />
        <button class="btn-sm" :disabled="loading" @click="addPoint">+ Add</button>
      </div>
    </div>

    <div v-if="team && points.length" class="path-table-wrap">
      <table class="path-table">
        <thead>
          <tr><th>Lat</th><th>Lon</th><th>Time</th><th></th></tr>
        </thead>
        <tbody>
          <tr v-for="(p, i) in points" :key="i">
            <td><CoordinateInput v-model="p.lat" axis="lat" compact /></td>
            <td><CoordinateInput v-model="p.lon" axis="lon" compact /></td>
            <td class="ts-cell">{{ fmtTs(p.timestamp) }}</td>
            <td><button class="btn-sm btn-del" @click="deletePoint(i)">✕</button></td>
          </tr>
        </tbody>
      </table>
      <button class="btn-save" :disabled="loading" @click="savePath">Save Changes</button>
    </div>

    <p v-if="loading" class="muted">Loading...</p>
  </div>
</template>

<style scoped>
.path-table-wrap {
  margin-top: 8px;
}

.path-table {
  width: 100%;
  font-size: 0.82rem;
}

.path-table th,
.path-table td {
  padding: 4px 6px;
}

.ts-cell {
  font-size: 0.72rem;
  color: var(--color-text-muted);
}

.btn-sm {
  padding: 4px 12px;
  font-size: 0.82rem;
}

.btn-del {
  background: none;
  border: 1px solid transparent;
  color: var(--color-text-muted);
  cursor: pointer;
  padding: 2px 6px;
}
.btn-del:hover {
  color: var(--color-accent-red);
  border-color: var(--color-accent-red);
}

.btn-save {
  margin-top: 8px;
  padding: 5px 16px;
  font-size: 0.85rem;
  background: var(--color-accent-red);
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
.btn-save:hover { background: var(--color-accent-orange); }

.add-point { margin-top: 10px; }
.add-row {
  display: flex;
  gap: 6px;
  align-items: center;
}
.add-row .coord-input { flex: 1; }
</style>
