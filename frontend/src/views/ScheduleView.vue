<script setup lang="ts">
import { computed, ref, onUnmounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useSchedule } from '@/api/useSchedule'
import { postSalvoTimer } from '@/api'
import ScheduleLane from '@/components/ScheduleLane.vue'

const auth = useAuthStore()
const isAdmin = computed(() => !!auth.user?.is_admin)

const { lanes, connected, lastUpdate, salvoTimerStarted, error, moveTeam, recallAll, updateTeamField } = useSchedule(isAdmin)

const pollLive = computed(() => lastUpdate.value !== null && Date.now() - lastUpdate.value < 30_000)

const now = ref(Date.now())
const tick = setInterval(() => { now.value = Date.now() }, 500)
onUnmounted(() => clearInterval(tick))

const timerDisplay = computed(() => {
  if (!salvoTimerStarted.value) return null
  const elapsed = Math.max(0, Math.floor((now.value - new Date(salvoTimerStarted.value).getTime()) / 1000))
  const m = Math.floor(elapsed / 60)
  const s = elapsed % 60
  return `T+${m}:${s.toString().padStart(2, '0')}`
})

async function startTimer() {
  if (!window.confirm('Start salvo timer?')) return
  const data = await postSalvoTimer('start')
  salvoTimerStarted.value = data.salvo_timer_started
}

async function clearTimer() {
  if (!window.confirm('Clear salvo timer?')) return
  await postSalvoTimer('clear')
  salvoTimerStarted.value = null
}

const teamMinSlots = computed(() => {
  const m = new Map<string, number>()
  for (const lane of lanes.value) {
    for (const t of lane.teams) {
      m.set(t.team_identifier, Math.ceil(t.fill_to_fire / 2))
    }
  }
  return m
})

function findLaneForTeam(teamId: string): string {
  for (const lane of lanes.value) {
    if (lane.teams.some(t => t.team_identifier === teamId)) return lane.id
  }
  return ''
}

function onLaneChange(laneId: string, event: { teamId: string; toIndex: number }) {
  const fromLaneId = findLaneForTeam(event.teamId)
  moveTeam(event.teamId, fromLaneId, laneId, event.toIndex)
  // If target is a salvo lane, use toIndex as the salvo_time slot
  if (laneId.startsWith('salvo')) {
    updateTeamField(event.teamId, 'salvo_time', event.toIndex)
  }
}

function autoSortSalvo(laneId: string) {
  const lane = lanes.value.find(l => l.id === laneId)
  if (!lane || !lane.teams.length) return
  // Sort by F2F ascending, tiebreak by hold_time ascending
  const sorted = [...lane.teams].sort((a, b) => {
    const f2f = a.fill_to_fire - b.fill_to_fire
    if (f2f !== 0) return f2f
    return a.hold_time - b.hold_time
  })
  const occupied = new Set<number>()
  for (const t of sorted) {
    const minSlot = Math.ceil(t.fill_to_fire / 2)
    let slot = Math.round(t.fill_to_fire / 2)
    slot = Math.max(minSlot, Math.min(25, slot))
    // If that slot is taken, find the next open one
    while (occupied.has(slot) && slot < 25) slot++
    occupied.add(slot)
    if (t.salvo_time !== slot) {
      updateTeamField(t.team_identifier, 'salvo_time', slot)
    }
  }
}

const currentLaneIndex = ref(0)
function prevLane() {
  if (currentLaneIndex.value > 0) currentLaneIndex.value--
}
function nextLane() {
  if (currentLaneIndex.value < lanes.value.length - 1) currentLaneIndex.value++
}
</script>

<template>
  <div class="schedule-view">
    <div class="schedule-header">
      <h1>Launch Schedule</h1>
      <div class="schedule-status">
        <span v-if="isAdmin && connected" class="badge badge-connected">Editing Live</span>
        <span v-else-if="isAdmin" class="badge badge-disconnected">Connecting...</span>
        <span v-else-if="error" class="badge badge-disconnected">{{ error }}</span>
        <span v-else-if="pollLive" class="badge badge-connected">Live</span>
        <span v-else class="badge badge-disconnected">Lost Connection</span>
        <span v-if="timerDisplay" class="badge badge-timer">{{ timerDisplay }}</span>
      </div>
      <div v-if="isAdmin" class="timer-controls">
        <button class="timer-btn" @click="startTimer">{{ salvoTimerStarted ? 'Reset' : 'Start' }} Timer</button>
        <button v-if="salvoTimerStarted" class="timer-btn timer-btn-clear" @click="clearTimer">Clear Timer</button>
      </div>
    </div>

    <div class="lanes-nav">
      <button class="lane-arrow" :disabled="currentLaneIndex === 0" @click="prevLane">◀</button>
      <span class="lane-nav-label">{{ lanes[currentLaneIndex]?.label }}</span>
      <button class="lane-arrow" :disabled="currentLaneIndex >= lanes.length - 1" @click="nextLane">▶</button>
    </div>
    <div class="lanes-container">
      <ScheduleLane
        v-for="(lane, i) in lanes"
        :key="lane.id"
        :lane="lane"
        :draggable="isAdmin"
        :on-update-field="updateTeamField"
        :team-min-slots="teamMinSlots"
        :class="{ 'lane-active': i === currentLaneIndex }"
        @change="(e) => onLaneChange(lane.id, e)"
        @auto-sort="autoSortSalvo(lane.id)"
        @recall-all="recallAll"
      />
    </div>
  </div>
</template>

<style scoped>
.schedule-view {
  padding: 0 20px 20px;
}

.schedule-header {
  display: flex;
  align-items: center;
  gap: 16px;
}

.schedule-header h1 {
  margin-bottom: 0;
}

.schedule-status {
  display: flex;
  align-items: center;
  gap: 8px;
}

.badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 600;
  transition: background 0.3s ease, color 0.3s ease;
}

.badge-connected {
  background: rgba(40, 167, 69, 0.85);
  color: #fff;
  backdrop-filter: blur(4px);
}

.badge-disconnected {
  background: rgba(255, 193, 7, 0.85);
  color: #333;
  backdrop-filter: blur(4px);
}

.badge-timer {
  background: rgba(192, 57, 43, 0.85);
  color: #fff;
  font-variant-numeric: tabular-nums;
  backdrop-filter: blur(4px);
}

.timer-controls {
  display: flex;
  gap: 6px;
}

.timer-btn {
  padding: 4px 12px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 5px;
  background: rgba(17, 17, 17, 0.6);
  color: #ccc;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.2s ease;
}
.timer-btn:hover {
  border-color: var(--color-accent-orange);
  color: var(--color-accent-orange);
  background: rgba(17, 17, 17, 0.8);
}


.lanes-nav {
  display: none;
}

.lanes-container {
  margin-top: 16px;
  display: flex;
  gap: 16px;
  overflow-x: auto;
  padding-bottom: 12px;
  align-items: stretch;
}

@media (max-width: 768px) {
  .schedule-header {
    flex-wrap: wrap;
    justify-content: space-between;
    gap: 8px;
  }
  .schedule-header h1 {
    width: 100%;
  }
  .schedule-status {
    flex-direction: column;
    align-items: flex-start;
  }
  .timer-controls {
    flex-direction: column;
    align-items: flex-end;
  }

  .lanes-nav {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    margin-top: 12px;
  }
  .lane-arrow {
    padding: 6px 14px;
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 6px;
    background: rgba(17, 17, 17, 0.6);
    color: #ccc;
    font-size: 1rem;
    cursor: pointer;
    transition: all 0.2s ease;
  }
  .lane-arrow:disabled {
    opacity: 0.3;
    cursor: default;
  }
  .lane-arrow:not(:disabled):hover {
    border-color: var(--color-accent-orange);
    color: var(--color-accent-orange);
  }
  .lane-nav-label {
    font-weight: 600;
    font-size: 0.95rem;
    color: var(--color-text);
    min-width: 100px;
    text-align: center;
  }
  .lanes-container {
    gap: 0;
  }
  .lanes-container :deep(.lane) {
    display: none;
    flex: 1;
  }
  .lanes-container :deep(.lane.lane-active) {
    display: flex;
  }
}
</style>
