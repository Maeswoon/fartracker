<script setup lang="ts">
import type { Team } from '@/types'

defineProps<{
  modelValue: string
  teams: Team[]
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()
</script>

<template>
  <select
    :value="modelValue"
    required
    @change="emit('update:modelValue', ($event.target as HTMLSelectElement).value)"
  >
    <option value="">Select team:</option>
    <option v-for="t in teams" :key="t.team_identifier" :value="t.team_identifier">{{ t.name }}</option>
  </select>
</template>
