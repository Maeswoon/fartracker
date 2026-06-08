<script setup lang="ts">
import { ref, watch } from 'vue'
import { getTeamRecovery, deleteRecoveryPiece, patchRecoveryPiece, postRecoveryPiece, postRecoveryPath } from '@/api'
import type { Team, RecoveryPiece } from '@/types'
import TeamSelect from '@/components/TeamSelect.vue'
import CoordinateInput from '@/components/CoordinateInput.vue'

const props = defineProps<{ teams: Team[] }>()
const emit = defineEmits<{ pathAdded: []; updated: [] }>()

const team = ref('')
const pieces = ref<RecoveryPiece[]>([])
const loading = ref(false)
const message = ref('')
const errorMsg = ref('')

const newName = ref('')
const newLat = ref(0)
const newLon = ref(0)
const alsoPath = ref(true)

async function loadPieces() {
  pieces.value = []
  errorMsg.value = ''
  if (!team.value) return
  loading.value = true
  try {
    pieces.value = await getTeamRecovery(team.value)
    message.value = ''
  } catch {
    errorMsg.value = 'Failed to load pieces.'
  } finally {
    loading.value = false
  }
}

watch(team, loadPieces)

async function handleDelete(pieceId: number) {
  if (!window.confirm('Delete this piece?')) return
  loading.value = true
  try {
    await deleteRecoveryPiece(team.value, pieceId)
    pieces.value = pieces.value.filter(p => p.id !== pieceId)
    message.value = 'Piece deleted.'
    emit('updated')
  } catch {
    errorMsg.value = 'Failed to delete piece.'
  } finally {
    loading.value = false
  }
}

async function savePiece(piece: RecoveryPiece) {
  loading.value = true
  errorMsg.value = ''
  try {
    await patchRecoveryPiece(team.value, piece.id, {
      object_name: piece.object_name,
      lat: piece.lat,
      lon: piece.lon,
    })
    message.value = 'Saved.'
    emit('updated')
  } catch {
    errorMsg.value = 'Failed to save.'
  } finally {
    loading.value = false
  }
}

async function handleAdd() {
  if (!team.value || !newName.value.trim()) {
    errorMsg.value = 'Please fill in all fields.'
    return
  }
  loading.value = true
  try {
    const name = newName.value.trim()
    await postRecoveryPiece(team.value, name, newLat.value, newLon.value)
    if (alsoPath.value) {
      await postRecoveryPath(team.value, newLat.value, newLon.value)
    }
    newName.value = ''
    newLat.value = 0
    newLon.value = 0
    await loadPieces()
    if (alsoPath.value) emit('pathAdded')
    emit('updated')
    message.value = 'Piece added.'
  } catch {
    errorMsg.value = 'Failed to add piece.'
  } finally {
    loading.value = false
  }
}

defineExpose({ refresh: loadPieces })
</script>

<template>
  <div class="form-card form-card--wide">
    <h3>Recovery Pieces</h3>
    <p v-if="message" class="success">{{ message }}</p>
    <p v-if="errorMsg" class="error">{{ errorMsg }}</p>

    <label>Team</label>
    <TeamSelect v-model="team" :teams="props.teams" />

    <div v-if="team" class="add-section">
      <div class="add-row">
        <input v-model="newName" type="text" placeholder="Object name" class="field-input" />
        <CoordinateInput v-model="newLat" axis="lat" compact />
        <CoordinateInput v-model="newLon" axis="lon" compact />
        <button class="btn-sm" :disabled="loading" @click="handleAdd">+ Add</button>
      </div>
      <label class="checkbox-label">
        <input v-model="alsoPath" type="checkbox" />
        Also publish to team path
      </label>
    </div>

    <div v-if="pieces.length" class="piece-list">
      <div v-for="piece in pieces" :key="piece.id" class="piece-row">
        <input v-model="piece.object_name" type="text" class="field-input" style="flex:1" />
        <CoordinateInput v-model="piece.lat" axis="lat" compact />
        <CoordinateInput v-model="piece.lon" axis="lon" compact />
        <button class="btn-sm" :disabled="loading" @click="savePiece(piece)">Save</button>
        <button class="btn-del" @click="handleDelete(piece.id)">✕</button>
      </div>
    </div>
    <p v-else-if="team && !loading && !errorMsg" class="muted">No pieces for this team.</p>
  </div>
</template>

<style scoped>
.add-section { margin-top: 10px; }
.add-row {
  display: flex;
  gap: 6px;
  align-items: center;
}

.field-input {
  padding: 4px 6px;
  font-size: 0.82rem;
  border: 1px solid var(--color-border);
  border-radius: 3px;
  background: var(--color-input-bg);
  color: var(--color-text);
  font-family: inherit;
}
.btn-sm {
  padding: 4px 12px;
  font-size: 0.82rem;
  white-space: nowrap;
}

.checkbox-label {
  margin-top: 8px;
  font-size: 0.8rem;
  display: flex;
  align-items: center;
  gap: 8px;
}

.piece-list {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-height: 300px;
  overflow-y: auto;
}

.piece-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 8px;
  border-radius: 4px;
  background: var(--color-surface-alt);
}

.btn-del {
  background: none;
  border: 1px solid transparent;
  color: var(--color-text-muted);
  cursor: pointer;
  padding: 2px 6px;
  font-size: 0.82rem;
}
.btn-del:hover {
  color: var(--color-accent-red);
  border-color: var(--color-accent-red);
}
</style>
