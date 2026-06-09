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
      <div class="flex gap-2">
        <div class="flex-1 flex gap-1.5 items-center flex-wrap piece-fields">
          <input v-model="newName" type="text" placeholder="Object name" class="field-input" style="max-width:200px" />
          <div class="flex gap-1.5 items-center">
            <CoordinateInput v-model="newLat" axis="lat" compact />
            <CoordinateInput v-model="newLon" axis="lon" compact />
          </div>
        </div>
        <button class="btn-sm self-center" :disabled="loading" @click="handleAdd">+ Add</button>
      </div>
      <label class="checkbox-label">
        <input v-model="alsoPath" type="checkbox" />
        Also publish to team path
      </label>
    </div>

    <div v-if="pieces.length" class="piece-list">
      <div v-for="piece in pieces" :key="piece.id" class="piece-row">
        <div class="flex-1 flex gap-1.5 items-center flex-wrap piece-fields">
          <input v-model="piece.object_name" type="text" class="field-input" style="max-width:200px" />
          <div class="flex gap-1.5 items-center">
            <CoordinateInput v-model="piece.lat" axis="lat" compact />
            <CoordinateInput v-model="piece.lon" axis="lon" compact />
          </div>
        </div>
        <div class="flex gap-1 items-center self-center">
          <button class="btn-sm" :disabled="loading" @click="savePiece(piece)">Save</button>
          <button class="btn-del" @click="handleDelete(piece.id)">✕</button>
        </div>
      </div>
    </div>
    <p v-else-if="team && !loading && !errorMsg" class="muted">No pieces for this team.</p>
  </div>
</template>

<style scoped>
@reference "tailwindcss";

.add-section { @apply mt-2.5; }

@media (max-width: 1200px) and (min-width: 901px) {
  .piece-fields { @apply flex-col items-start; }
}
@media (max-width: 400px) {
  .piece-fields { @apply flex-col items-start; }
}

.field-input {
  @apply py-1 px-1.5 text-[0.82rem] border border-(--color-border) rounded-sm min-w-[120px];
  font-family: inherit;
  background: var(--color-input-bg);
  color: var(--color-text);
}
.btn-sm { @apply py-1 px-3 text-[0.82rem] whitespace-nowrap; }
.checkbox-label { @apply mt-2 text-xs flex items-center gap-2; }

.piece-list { @apply mt-2.5 flex flex-col gap-1 max-h-[300px] overflow-y-auto; }
.piece-row {
  @apply flex gap-2 py-1 px-2 rounded;
  background: var(--color-surface-alt);
}

.btn-del {
  @apply bg-transparent border border-transparent text-(--color-text-muted) cursor-pointer py-1 px-1.5 text-[0.82rem];
}
.btn-del:hover {
  @apply text-(--color-accent-red) border-(--color-accent-red);
}
</style>
