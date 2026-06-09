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
  <div :class="['team-card', { 'is-draggable': draggable }]">
    <div class="team-card-header">
      <div class="team-name">{{ team.name }}</div>
      <span class="engine-badge">{{ team.engine_type }}</span>
    </div>
    <div class="team-meta">{{ team.university }} · Cat {{ team.category }}</div>
    <div class="team-timing">
      <template v-if="draggable">
        <label class="timing-field">
          F2F
          <input type="number" step="0.5" min="0" class="timing-input" :value="team.fill_to_fire" @change="onInput('fill_to_fire', $event)" />m
        </label>
        <label class="timing-field">
          Hold
          <input type="number" step="0.5" min="0" class="timing-input" :value="team.hold_time" @change="onInput('hold_time', $event)" />m
        </label>
      </template>
      <template v-else>
        <span class="timing-field">F2F&nbsp;<span class="timing-value">{{ team.fill_to_fire }}</span>m</span>
        <span class="timing-sep">&middot;</span>
        <span class="timing-field">Hold&nbsp;<span class="timing-value">{{ team.hold_time }}</span>m</span>
        <span class="timing-sep">&middot;</span>
      </template>
      <span class="timing-field delay-field">+{{ delay }}m</span>
      <span v-if="saving" class="saving-dot" />
    </div>
  </div>
</template>

<style scoped>
.team-card {
  --card-muted: var(--color-text-muted);
  background: var(--color-card);
  border-radius: 6px;
  padding: 5px 8px;
  border: 1px solid var(--color-border);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.15);
  color: var(--color-text);
  font-size: 0.95rem;
}

.team-card.is-draggable {
  cursor: grab;
  user-select: none;
}

.team-card.is-draggable:active {
  cursor: grabbing;
}

.team-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.team-name {
  font-weight: 600;
}

.engine-badge {
  font-size: 0.68rem;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 6px;
  white-space: nowrap;
  margin-left: 6px;
  flex-shrink: 0;
  background: var(--color-nav-bg);
  color: var(--color-accent-red);
  border: 1px solid var(--color-accent-red);
}

.team-meta {
  font-size: 0.78rem;
  color: var(--card-muted);
  margin-top: 1px;
}

.team-timing {
  display: flex;
  gap: 4px;
  margin-top: 3px;
  align-items: center;
}

.timing-field {
  font-size: 0.74rem;
  color: var(--card-muted);
  display: flex;
  align-items: center;
  gap: 1px;
}

.timing-input {
  width: 40px;
  padding: 1px 3px;
  font-size: 0.72rem;
  border: 1px solid #555;
  border-radius: 3px;
  background: var(--color-nav-bg);
  color: var(--color-text);
  text-align: right;
  font-family: inherit;
}

.timing-input:not([readonly]):focus {
  border-color: var(--color-accent-red);
  outline: none;
}

.timing-sep {
  color: var(--card-muted);
  font-size: 0.6rem;
}

.timing-value {
  font-weight: 600;
  color: var(--card-muted);
}

.delay-field {
  color: var(--color-accent-red);
  font-weight: 600;
}

.saving-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-accent-red);
  animation: pulse 0.6s infinite alternate;
}

@keyframes pulse {
  to { opacity: 0.3; }
}
</style>
