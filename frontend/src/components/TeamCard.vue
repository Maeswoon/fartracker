<script setup lang="ts">
import { computed, ref } from 'vue'
import type { ScheduleTeam } from '@/types'

const props = defineProps<{
  team: ScheduleTeam
  laneLabel: string
  draggable?: boolean
  onUpdateField: (teamId: string, field: string, value: number) => void
}>()

const saving = ref(false)

const delay = computed(() => Math.max(0, props.team.salvo_time * 2 - props.team.fill_to_fire))

const fractions = Array.from({ length: 7 }, (_, n) => ({
  label: n === 0 ? '1' : `1/${2 ** n}`,
  value: n,
}))

function setFraction(pos: number, event: MouseEvent) {
  if (event.ctrlKey || event.metaKey) {
    // ctrl+click: erase this position and all to the right
    const cur = props.team.modifier_fraction ?? -1
    const newVal = pos - 1
    const capped = cur >= 0 && newVal > cur ? cur : newVal
    const label = capped >= 0 ? fractions[capped].label : 'none'
    if (!window.confirm(`Clear modifier fraction down to ${label}?`)) return
    saving.value = true
    props.onUpdateField(props.team.team_identifier, 'modifier_fraction', capped)
    setTimeout(() => { saving.value = false }, 300)
    return
  }
  if (!window.confirm(`Set modifier fraction to ${fractions[pos].label}?`)) return
  saving.value = true
  props.onUpdateField(props.team.team_identifier, 'modifier_fraction', pos)
  setTimeout(() => { saving.value = false }, 300)
}

function updateField(field: 'fill_to_fire' | 'hold_time' | 'salvo_time', value: string) {
  const num = parseFloat(value)
  if (isNaN(num) || num < 0) return
  saving.value = true
  props.onUpdateField(props.team.team_identifier, field, num)
  setTimeout(() => { saving.value = false }, 300)
}

function onInput(field: 'fill_to_fire' | 'hold_time' | 'salvo_time', event: Event) {
  const input = event.target as HTMLInputElement
  updateField(field, input.value)
}
</script>

<template>
  <div :class="['bg-(--color-card) rounded-md p-[5px_8px] border border-(--color-border) text-(--color-text) text-[0.95rem] shadow-sm', { 'cursor-grab select-none active:cursor-grabbing': draggable }]">
    <div class="flex justify-between items-center">
      <div class="font-semibold">{{ team.name }}</div>
      <span class="text-[0.68rem] font-semibold py-px px-1.5 rounded-md whitespace-nowrap ml-1.5 shrink-0 bg-(--color-nav-bg) text-(--color-accent-red) border border-(--color-accent-red)">{{ team.engine_type }}</span>
    </div>
    <div class="text-xs text-(--color-text-muted) mt-px">{{ team.university }} · Cat {{ team.category }}</div>
    <div class="flex gap-1 mt-0.5 items-center">
      <template v-if="draggable">
        <label class="text-xs text-(--color-text-muted) flex items-center gap-px">
          F2F
          <input type="number" step="0.5" min="0" class="timing-input" :value="team.fill_to_fire" @change="onInput('fill_to_fire', $event)" />m
        </label>
        <label class="text-xs text-(--color-text-muted) flex items-center gap-px">
          Hold
          <input type="number" step="0.5" min="0" class="timing-input" :value="team.hold_time" @change="onInput('hold_time', $event)" />m
        </label>
      </template>
      <template v-else>
        <span class="text-xs text-(--color-text-muted) flex items-center gap-px">F2F&nbsp;<span class="font-semibold text-(--color-text-muted)">{{ team.fill_to_fire }}</span>m</span>
        <span class="text-[0.6rem] text-(--color-text-muted)">&middot;</span>
        <span class="text-xs text-(--color-text-muted) flex items-center gap-px">Hold&nbsp;<span class="font-semibold text-(--color-text-muted)">{{ team.hold_time }}</span>m</span>
        <span class="text-[0.6rem] text-(--color-text-muted)">&middot;</span>
      </template>
      <span class="text-xs text-(--color-accent-red) font-semibold">+{{ delay }}m</span>
      <span v-if="saving" class="w-1.5 h-1.5 rounded-full bg-(--color-accent-red) animate-pulse" />
    </div>
    <div v-if="draggable" class="flex gap-px mt-0.5">
      <button
        v-for="f in fractions"
        :key="f.value"
        class="fraction-btn"
        :class="{ checked: team.modifier_fraction != null && f.value <= team.modifier_fraction }"
        @click="(e: MouseEvent) => setFraction(f.value, e)"
      >{{ f.label }}</button>
    </div>
  </div>
</template>

<style scoped>
.timing-input {
  width: 40px;
  padding: 1px 3px;
  font-size: 0.72rem;
  border: 1px solid var(--color-toggle-off);
  border-radius: 3px;
  background: var(--color-nav-bg);
  color: var(--color-text);
  text-align: right;
  font-family: inherit;
}
.timing-input:focus {
  border-color: var(--color-accent-red);
  outline: none;
}

.fraction-btn {
  font-size: 0.6rem;
  padding: 0 3px;
  min-width: 22px;
  height: 16px;
  border: 1px solid var(--color-border);
  border-radius: 2px;
  background: var(--color-nav-bg);
  color: var(--color-text-muted);
  cursor: pointer;
  font-family: inherit;
  line-height: 1;
  transition: all 0.15s ease;
}
.fraction-btn.checked {
  background: var(--color-accent-red);
  border-color: var(--color-accent-red);
  color: #fff;
  text-decoration: line-through;
}
</style>
