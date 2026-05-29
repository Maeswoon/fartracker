<script setup lang="ts">
import { ref, watch } from 'vue'
import { getFrequencies, patchTeamFrequencies } from '@/api'
import { useForm } from '@/api/useApi'
import type { Team, GpsFrequencies } from '@/types'
import TeamSelect from '@/components/TeamSelect.vue'

const props = defineProps<{ teams: Team[] }>()

const { success, error, submit } = useForm()

const team = ref('')
const fields = ref<GpsFrequencies>({ avionics: '', gse: '', team_comms: '' })

async function loadFrequencies() {
  if (!team.value) return
  error.value = null
  try {
    const all = await getFrequencies()
    const match = all.find(f => f.team_identifier === team.value)
    const existing: Partial<GpsFrequencies> = match?.gps_frequencies ?? {}
    fields.value = {
      avionics: existing.avionics ?? '',
      gse: existing.gse ?? '',
      team_comms: existing.team_comms ?? '',
    }
  } catch {
    error.value = 'Failed to load frequencies.'
  }
}

watch(team, loadFrequencies)

function handleSubmit() {
  if (!team.value) {
    error.value = 'Please select a team.'
    return
  }
  submit(() => patchTeamFrequencies(team.value, fields.value), 'Failed to update frequencies.')
}
</script>

<template>
  <div class="form-card">
    <h3>Set Team Frequencies</h3>
    <p v-if="success" class="success">Frequencies updated!</p>
    <p v-if="error" class="error">{{ error }}</p>
    <form @submit.prevent="handleSubmit">
      <label>Team</label>
      <TeamSelect v-model="team" :teams="props.teams" />
      <template v-if="team">
        <label>Avionics</label>
        <input v-model="fields.avionics" type="text" placeholder="e.g. 433.5 MHz" />
        <label>GSE</label>
        <input v-model="fields.gse" type="text" placeholder="e.g. 915.0 MHz" />
        <label>Team Comms</label>
        <input v-model="fields.team_comms" type="text" placeholder="e.g. 462.5625 MHz" />
        <button type="submit">Save</button>
      </template>
    </form>
  </div>
</template>
