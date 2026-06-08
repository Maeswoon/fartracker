<script setup lang="ts">
defineProps<{
  modelValue: number
  axis: 'lat' | 'lon'
  compact?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: number]
}>()

const label = { lat: 'Latitude', lon: 'Longitude' }
const short = { lat: 'Lat', lon: 'Lon' }
const dir = (value: number, axis: 'lat' | 'lon') => {
  return axis === 'lat' ? (value >= 0 ? 'N' : 'S') : (value >= 0 ? 'E' : 'W')
}
</script>

<template>
  <label v-if="!compact">
    {{ label[axis] }} <span class="direction">({{ dir(modelValue, axis) }})</span>
    <input
      type="number" step="any" required
      :value="modelValue"
      @input="emit('update:modelValue', ($event.target as HTMLInputElement).valueAsNumber)"
    />
  </label>
  <span v-else class="coord-inline">
    <input
      type="number" step="any"
      class="coord-input"
      :placeholder="short[axis]"
      :value="modelValue"
      @input="emit('update:modelValue', ($event.target as HTMLInputElement).valueAsNumber)"
    />
    <span class="axis-hint">{{ dir(modelValue, axis) }}</span>
  </span>
</template>

<style scoped>
.direction { font-size: 0.8rem; color: var(--color-text-muted); }

.coord-inline {
  display: inline-flex;
  align-items: center;
  gap: 2px;
}

.coord-input {
  width: 80px;
  padding: 2px 4px;
  font-size: 0.78rem;
  border: 1px solid var(--color-border);
  border-radius: 3px;
  background: var(--color-input-bg);
  color: var(--color-text);
  font-family: inherit;
}

.axis-hint {
  font-size: 0.78rem;
  color: var(--color-text-muted);
  width: 18px;
}
</style>
