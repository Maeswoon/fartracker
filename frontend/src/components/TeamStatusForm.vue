<script setup lang="ts">
import { ref, computed } from 'vue'
import { postTeamStatus } from '@/api'
import { useForm } from '@/api/useApi'
import type { Team } from '@/types'
import TeamSelect from '@/components/TeamSelect.vue'

const props = defineProps<{ teams: Team[] }>()

const { success, error, submit } = useForm()

const team = ref('')
const status = ref('')
const padName = ref('')
const statusOptions = ['Absent', 'Onsite', 'At rail', 'In salvo', 'In recovery', 'Recovered']
const padStatuses = ['At rail', 'In salvo']
const showPad = computed(() => padStatuses.includes(status.value))

function handleSubmit() {
  submit(async () => {
    await postTeamStatus(team.value, status.value, padName.value || undefined)
    status.value = ''
    padName.value = ''
  }, 'Failed to post status.')
}
</script>

<template>
  <div class="form-card">
    <h3>Set Team Status</h3>
    <p v-if="success" class="success">Status posted!</p>
    <p v-if="error" class="error">{{ error }}</p>
    <form @submit.prevent="handleSubmit">
      <label>Team</label>
      <TeamSelect v-model="team" :teams="props.teams" />
      <label>Status</label>
      <select v-model="status" required>
        <option value="">Select status:</option>
        <option v-for="s in statusOptions" :key="s" :value="s">{{ s }}</option>
      </select>
      <template v-if="showPad">
        <label>Pad Name</label>
        <input v-model="padName" type="text" placeholder="e.g. Rail 3" />
      </template>
      <button type="submit">Post</button>
    </form>
  </div>
</template>
