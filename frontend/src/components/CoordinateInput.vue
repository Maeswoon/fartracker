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
    {{ label[axis] }} <span class="text-xs text-(--color-text-muted)">({{ dir(modelValue, axis) }})</span>
    <input
      type="number" step="any" required
      :value="modelValue"
      @input="emit('update:modelValue', ($event.target as HTMLInputElement).valueAsNumber)"
    />
  </label>
  <span v-else class="inline-flex items-center gap-0.5">
    <input
      type="number" step="any"
      class="py-0.5 px-1 text-xs border border-(--color-border) rounded-sm bg-(--color-input-bg) text-(--color-text)" style="font-family:inherit;width:8ch;min-width:0;flex:none"
      :placeholder="short[axis]"
      :value="modelValue"
      @input="emit('update:modelValue', ($event.target as HTMLInputElement).valueAsNumber)"
    />
    <span class="text-xs text-(--color-text-muted) w-[18px]">{{ dir(modelValue, axis) }}</span>
  </span>
</template>
