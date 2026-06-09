<script setup lang="ts">
import { computed, ref, watch, onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useSchedule } from '@/api/useSchedule'
import { postSalvoTimer } from '@/api'
import ScheduleLane from '@/components/ScheduleLane.vue'

const auth = useAuthStore()
const isAdmin = computed(() => !!auth.user?.is_admin)

const { lanes, connected, lastUpdate, salvoTimerStarted, error, moveTeam, recallAll, updateTeamField, setTimerYjs } = useSchedule(isAdmin)

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
  setTimerYjs(data.salvo_timer_started)
}

async function clearTimer() {
  if (!window.confirm('Clear salvo timer?')) return
  await postSalvoTimer('clear')
  salvoTimerStarted.value = null
  setTimerYjs(null)
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

// ── Responsive lane pagination ──
const windowWidth = ref(window.innerWidth)
const lanesPerView = computed(() => {
  if (windowWidth.value <= 600) return 1
  if (windowWidth.value <= 1250) return 2
  return lanes.value.length
})
const maxLaneIndex = computed(() => Math.max(0, lanes.value.length - lanesPerView.value))
const currentLaneIndex = ref(0)

watch(lanesPerView, () => {
  if (currentLaneIndex.value > maxLaneIndex.value) {
    currentLaneIndex.value = maxLaneIndex.value
  }
})

function onWindowResize() { windowWidth.value = window.innerWidth }
onMounted(() => window.addEventListener('resize', onWindowResize))
onUnmounted(() => window.removeEventListener('resize', onWindowResize))

function prevLane() {
  if (currentLaneIndex.value > 0) currentLaneIndex.value--
}
function nextLane() {
  if (currentLaneIndex.value < maxLaneIndex.value) currentLaneIndex.value++
}

// ── Edge-triggered lane switching during drag ──
const isDragging = ref(false)
const edgeZone = ref<'left' | 'right' | null>(null)
let edgeTimer: ReturnType<typeof setTimeout> | null = null
let cooldownTimer: ReturnType<typeof setTimeout> | null = null
const EDGE_DEBOUNCE = 500   // ms hovering at edge before switching
const EDGE_COOLDOWN = 400   // ms before another switch is allowed
const EDGE_FRACTION = 0.12  // fraction of viewport width from edge

function onDragStart() {
  isDragging.value = true
  document.addEventListener('pointermove', onPointerMove)
}

function onDragEnd() {
  isDragging.value = false
  edgeZone.value = null
  document.removeEventListener('pointermove', onPointerMove)
  if (edgeTimer) { clearTimeout(edgeTimer); edgeTimer = null }
  if (cooldownTimer) { clearTimeout(cooldownTimer); cooldownTimer = null }
}

function onPointerMove(e: PointerEvent) {
  const threshold = window.innerWidth * EDGE_FRACTION
  let zone: 'left' | 'right' | null = null
  if (e.clientX < threshold) zone = 'left'
  else if (e.clientX > window.innerWidth - threshold) zone = 'right'

  if (zone !== edgeZone.value) {
    edgeZone.value = zone
    if (edgeTimer) { clearTimeout(edgeTimer); edgeTimer = null }

    if (zone && !cooldownTimer) {
      edgeTimer = setTimeout(() => {
        if (zone === 'left') prevLane()
        else nextLane()
        edgeTimer = null
        edgeZone.value = null
        cooldownTimer = setTimeout(() => { cooldownTimer = null }, EDGE_COOLDOWN)
      }, EDGE_DEBOUNCE)
    }
  }
}

// Safety: clean up if component unmounts mid-drag
onUnmounted(() => {
  document.removeEventListener('pointermove', onPointerMove)
  if (edgeTimer) clearTimeout(edgeTimer)
  if (cooldownTimer) clearTimeout(cooldownTimer)
})
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

    <div v-if="lanesPerView < lanes.length" class="lanes-nav">
      <button class="lane-arrow prev" :class="{ 'arrow-hot': edgeZone === 'left' && currentLaneIndex > 0 }" :disabled="currentLaneIndex === 0" aria-label="Previous lane" @click="prevLane" />
      <span class="lane-nav-label">{{ lanes[currentLaneIndex]?.label }}</span>
      <button class="lane-arrow next" :class="{ 'arrow-hot': edgeZone === 'right' && currentLaneIndex < maxLaneIndex }" :disabled="currentLaneIndex >= maxLaneIndex" aria-label="Next lane" @click="nextLane" />
    </div>
    <div class="lanes-container" :class="{ 'lanes-paginated': lanesPerView < lanes.length }">
      <ScheduleLane
        v-for="(lane, i) in lanes"
        :key="lane.id"
        :lane="lane"
        :draggable="isAdmin"
        :on-update-field="updateTeamField"
        :team-min-slots="teamMinSlots"
        :class="{ 'lane-visible': i >= currentLaneIndex && i < currentLaneIndex + lanesPerView }"
        @change="(e) => onLaneChange(lane.id, e)"
        @auto-sort="autoSortSalvo(lane.id)"
        @recall-all="recallAll"
        @drag-start="onDragStart"
        @drag-end="onDragEnd"
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
  border-color: var(--color-accent-red);
  color: var(--color-accent-red);
  background: rgba(17, 17, 17, 0.8);
}


.lanes-nav {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-top: 12px;
}
.lane-arrow {
  width: 44px;
  height: 34px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(255,255,255,0.15);
  border-radius: 6px;
  background: rgba(17, 17, 17, 0.6);
  color: #ccc;
  cursor: pointer;
  transition: all 0.2s ease;
}
.lane-arrow::after {
  content: '';
  display: block;
  width: 9px;
  height: 9px;
  border-color: currentColor;
  border-style: solid;
  border-width: 0;
}
.lane-arrow.prev::after {
  border-left-width: 2px;
  border-bottom-width: 2px;
  transform: rotate(45deg);
  margin-right: -3px;
}
.lane-arrow.next::after {
  border-top-width: 2px;
  border-right-width: 2px;
  transform: rotate(45deg);
  margin-left: -3px;
}
.lane-arrow:disabled {
  opacity: 0.3;
  cursor: default;
}
.lane-arrow:not(:disabled):hover {
  border-color: var(--color-accent-red);
  color: var(--color-accent-red);
}
.lane-arrow.arrow-hot {
  border-color: var(--color-accent-red);
  color: var(--color-accent-red);
  animation: arrow-pulse 0.45s ease-in-out infinite alternate;
}
@keyframes arrow-pulse {
  from { transform: scale(1); }
  to   { transform: scale(1.18); }
}
.lane-nav-label {
  font-weight: 600;
  font-size: 0.95rem;
  color: var(--color-text);
  width: 120px;
  text-align: center;
}

.lanes-container {
  margin-top: 16px;
  display: flex;
  gap: 16px;
  overflow-x: auto;
  padding-bottom: 12px;
  align-items: stretch;
}

/* Paginated: only show lanes within the current window */
.lanes-paginated {
  gap: 8px;
  overflow-x: visible;
}
.lanes-paginated :deep(.lane) {
  display: none;
  flex: 1;
}
.lanes-paginated :deep(.lane.lane-visible) {
  display: flex;
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
}
</style>
