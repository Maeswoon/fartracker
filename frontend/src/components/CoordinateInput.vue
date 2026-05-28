<script setup lang="ts">
defineProps<{
  modelValue: number
  axis: 'lat' | 'lon'
}>()

const emit = defineEmits<{
  'update:modelValue': [value: number]
}>()

const label = { lat: 'Latitude', lon: 'Longitude' }
const direction = (value: number, axis: 'lat' | 'lon') => {
  if (!value) return '—'
  return axis === 'lat' ? (value > 0 ? 'N' : 'S') : (value > 0 ? 'E' : 'W')
}
</script>

<template>
  <div>
    <label>{{ label[axis] }} <span class="direction">({{ direction(modelValue, axis) }})</span></label>
    <input
      type="number"
      step="any"
      required
      :value="modelValue"
      @input="emit('update:modelValue', ($event.target as HTMLInputElement).valueAsNumber)"
    />
  </div>
</template>
