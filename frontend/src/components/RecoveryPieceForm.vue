<script setup lang="ts">
import { ref } from 'vue'
import { postRecoveryPiece, postRecoveryPath } from '@/api'
import { useForm } from '@/api/useApi'
import type { Team } from '@/types'
import TeamSelect from '@/components/TeamSelect.vue'
import CoordinateInput from '@/components/CoordinateInput.vue'

const props = defineProps<{ teams: Team[] }>()

const emit = defineEmits<{ submitted: [teamId: string] }>()

const { success, error, submit } = useForm()

const team = ref('')
const objectName = ref('')
const lat = ref<number>(0)
const lon = ref<number>(0)
const alsoPath = ref(true)

function handleSubmit() {
  if (!team.value || !objectName.value.trim()) {
    error.value = 'Please fill in all fields.'
    return
  }
  submit(async () => {
    await postRecoveryPiece(team.value, objectName.value, lat.value, lon.value)
    if (alsoPath.value) {
      await postRecoveryPath(team.value, lat.value, lon.value)
    }
    emit('submitted', team.value)
    objectName.value = ''
    lat.value = 0
    lon.value = 0
  }, 'Failed to add recovery piece.')
}
</script>

<template>
  <div class="form-card">
    <h3>Add Recovery Piece</h3>
    <p v-if="success" class="success">Recovery piece added!</p>
    <p v-if="error" class="error">{{ error }}</p>
    <form @submit.prevent="handleSubmit">
      <label>Team</label>
      <TeamSelect v-model="team" :teams="props.teams" />
      <label>Object Name</label>
      <input v-model="objectName" type="text" required />
      <CoordinateInput v-model="lat" axis="lat" />
      <CoordinateInput v-model="lon" axis="lon" />
      <label class="checkbox-label">
        <input v-model="alsoPath" type="checkbox" />
        Also publish to team path
      </label>
      <button type="submit">Submit</button>
    </form>
  </div>
</template>

<style scoped>
.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 8px 0 16px;
  font-weight: 500;
}

.checkbox-label input[type="checkbox"] {
  box-sizing: border-box;
  width: 22px;
  height: 22px;
  margin: 0;
  padding: 0;
  background-color: #fff;
  border: 2px solid var(--color-text-on-light);
  border-radius: 4px;
  appearance: none;
  -webkit-appearance: none;
  cursor: pointer;
  position: relative;
  flex-shrink: 0;
  display: inline-grid;
  place-content: center;
}

.checkbox-label input[type="checkbox"]:checked {
  background-color: var(--color-accent-red);
  border-color: var(--color-accent-red);
}

.checkbox-label input[type="checkbox"]:checked::after {
  content: '';
  display: block;
  width: 6px;
  height: 11px;
  border: solid #fff;
  border-width: 0 2.5px 2.5px 0;
  transform: translateY(-1px) rotate(45deg);
}
</style>
