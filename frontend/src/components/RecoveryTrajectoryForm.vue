<script setup lang="ts">
import { ref } from 'vue'
import { postRecoveryTrajectory } from '@/api'
import { useForm } from '@/api/useApi'
import type { Team } from '@/types'
import TeamSelect from '@/components/TeamSelect.vue'
import CoordinateInput from '@/components/CoordinateInput.vue'

const props = defineProps<{ teams: Team[] }>()

const { success, error, submit } = useForm()

const team = ref('')
const lat = ref<number>(0)
const lon = ref<number>(0)

function handleSubmit() {
  if (!team.value) {
    error.value = 'Please select a team.'
    return
  }
  submit(async () => {
    await postRecoveryTrajectory(team.value, lat.value, lon.value)
    lat.value = 0
    lon.value = 0
  }, 'Failed to add trajectory.')
}
</script>

<template>
  <div class="form-card">
    <h3>Add Recovery Trajectory</h3>
    <p v-if="success" class="success">Trajectory added!</p>
    <p v-if="error" class="error">{{ error }}</p>
    <form @submit.prevent="handleSubmit">
      <label>Team</label>
      <TeamSelect v-model="team" :teams="props.teams" />
      <CoordinateInput v-model="lat" axis="lat" />
      <CoordinateInput v-model="lon" axis="lon" />
      <button type="submit">Submit</button>
    </form>
  </div>
</template>
