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
  margin: 8px 0 16px;
}
</style>
