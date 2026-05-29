<script setup lang="ts">
import { ref, watch } from 'vue'
import { getTeamRecovery, deleteRecoveryPiece } from '@/api'
import { useForm } from '@/api/useApi'
import type { Team, RecoveryPiece } from '@/types'
import TeamSelect from '@/components/TeamSelect.vue'

const props = defineProps<{ teams: Team[] }>()

const { success, error, submit } = useForm()

const team = ref('')
const pieces = ref<RecoveryPiece[]>([])
const piecesLoading = ref(false)

async function loadPieces() {
  pieces.value = []
  error.value = null
  if (!team.value) return
  piecesLoading.value = true
  try {
    pieces.value = await getTeamRecovery(team.value)
  } catch {
    error.value = 'Failed to load recovery pieces.'
  } finally {
    piecesLoading.value = false
  }
}

watch(team, loadPieces)

async function handleDelete(pieceId: number) {
  if (!team.value) return
  submit(async () => {
    await deleteRecoveryPiece(team.value, pieceId)
    pieces.value = pieces.value.filter(p => p.id !== pieceId)
  }, 'Failed to delete piece.')
}

defineExpose({ refresh: loadPieces })
</script>

<template>
  <div class="form-card">
    <h3>Delete Recovery Piece</h3>
    <p v-if="success" class="success">Piece deleted.</p>
    <p v-if="error" class="error">{{ error }}</p>
    <form @submit.prevent>
      <label>Team</label>
      <TeamSelect v-model="team" :teams="props.teams" />
    </form>
    <div v-if="pieces.length" class="piece-list">
      <div v-for="piece in pieces" :key="piece.id" class="piece-row">
        <span class="muted">{{ piece.object_name }} ({{ piece.lat }}, {{ piece.lon }})</span>
        <button class="btn-delete" @click="handleDelete(piece.id)">Delete</button>
      </div>
    </div>
    <p v-else-if="team && !piecesLoading && !error" class="muted">No recovery pieces for this team.</p>
  </div>
</template>

<style scoped>
.piece-list {
  margin-top: 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 300px;
  overflow-y: auto;
}

.piece-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #f5f5f5;
  padding: 8px 10px;
  border-radius: 4px;
}

.btn-delete {
  background-color: #dc3545;
  color: white;
  border: none;
  padding: 4px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.85rem;
}

.btn-delete:hover {
  background-color: #c82333;
}
</style>
