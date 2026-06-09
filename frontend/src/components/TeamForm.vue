<script setup lang="ts">
import { ref } from 'vue'
import { getTeam, postTeam, patchTeam } from '@/api'
import { useForm } from '@/api/useApi'
import type { Team } from '@/types'
import TeamSelect from '@/components/TeamSelect.vue'

const props = defineProps<{ teams: Team[] }>()

const emit = defineEmits<{ updated: [] }>()

const { success, error, submit } = useForm()

const mode = ref<'new' | 'edit'>('edit')
const teamId = ref('')
const fields = ref({
  name: '', university: '', team_identifier: '',
  category: '', engine_type: '', fuel_oxidizer: '', target_altitude: '' as string | number,
})
const categoryOptions = [{ value: 'A', label: 'Category A' }, { value: 'B', label: 'Category B' }, { value: 'C', label: 'Category C' }, { value: 'E', label: 'Category Ex' }]
const engineTypeOptions = [{ value: 'H', label: 'Hybrid' }, { value: 'L', label: 'Liquid' }]

function reset() {
  fields.value = { name: '', university: '', team_identifier: '', category: '', engine_type: '', fuel_oxidizer: '', target_altitude: '' }
  teamId.value = ''
  success.value = false
  error.value = null
}

async function loadTeam() {
  if (!teamId.value) return
  error.value = null
  try {
    const team = await getTeam(teamId.value) as any
    fields.value = {
      name: team.name ?? '',
      university: team.university ?? '',
      team_identifier: team.team_identifier ?? '',
      category: team.category ?? '',
      engine_type: team.engine_type ?? '',
      fuel_oxidizer: team.fuel_oxidizer ?? '',
      target_altitude: team.target_altitude ?? '',
    }
  } catch {
    error.value = 'Failed to load team.'
  }
}

function handleSubmit() {
  const payload = {
    ...fields.value,
    target_altitude: fields.value.target_altitude !== '' ? Number(fields.value.target_altitude) : null,
  }
  const isNew = mode.value === 'new'
  submit(async () => {
    if (isNew) {
      await postTeam(payload)
      reset()
      emit('updated')
    } else {
      await patchTeam(teamId.value, payload)
      emit('updated')
    }
  }, isNew ? 'Failed to create team.' : 'Failed to update team.')
}
</script>

<template>
  <div class="form-card form-card--wide">
    <h3>Add / Edit Team</h3>
    <p v-if="success" class="success">{{ mode === 'new' ? 'Team created!' : 'Team updated!' }}</p>
    <p v-if="error" class="error">{{ error }}</p>
    <div class="mode-toggle">
      <button type="button" :class="{ active: mode === 'new' }" @click="mode = 'new'; reset()">New Team</button>
      <button type="button" :class="{ active: mode === 'edit' }" @click="mode = 'edit'; reset()">Edit Team</button>
    </div>
    <form @submit.prevent="handleSubmit" class="team-form-grid">
      <template v-if="mode === 'edit'">
        <div class="field-full">
          <label>Team</label>
          <TeamSelect v-model="teamId" :teams="props.teams" @update:model-value="loadTeam()" />
        </div>
      </template>
      <div>
        <label>Name</label>
        <input v-model="fields.name" type="text" required />
      </div>
      <div>
        <label>University</label>
        <input v-model="fields.university" type="text" required />
      </div>
      <template v-if="mode === 'new'">
        <div>
          <label>Team Identifier</label>
          <input v-model="fields.team_identifier" type="text" required />
        </div>
      </template>
      <div>
        <label>Category</label>
        <select v-model="fields.category" required>
          <option value="">Select:</option>
          <option v-for="o in categoryOptions" :key="o.value" :value="o.value">{{ o.label }}</option>
        </select>
      </div>
      <div>
        <label>Engine Type</label>
        <select v-model="fields.engine_type" required>
          <option value="">Select:</option>
          <option v-for="o in engineTypeOptions" :key="o.value" :value="o.value">{{ o.label }}</option>
        </select>
      </div>
      <div>
        <label>Fuel / Oxidizer</label>
        <input v-model="fields.fuel_oxidizer" type="text" />
      </div>
      <div>
        <label>Target Altitude (ft)</label>
        <input v-model="fields.target_altitude" type="number" />
      </div>
      <div class="field-full">
        <button type="submit">{{ mode === 'new' ? 'Create' : 'Save' }}</button>
      </div>
    </form>
  </div>
</template>

<style scoped>
@reference "tailwindcss";

.form-card--wide {
  @apply w-full max-w-[640px];
}

.team-form-grid {
  @apply grid grid-cols-2 gap-x-4;
}
.team-form-grid .field-full {
  @apply col-span-full;
}
.team-form-grid input,
.team-form-grid select {
  @apply w-full;
}
@media (max-width: 600px) {
  .team-form-grid {
    @apply grid-cols-1;
  }
}

.mode-toggle {
  @apply flex gap-2 mb-3.5;
}
.mode-toggle button {
  @apply flex-1 border-(--color-border);
  background-color: var(--color-input-bg);
  color: var(--color-text);
}
.mode-toggle button.active {
  @apply text-white border-(--color-accent-red);
  background-color: var(--color-accent-red);
}
</style>
