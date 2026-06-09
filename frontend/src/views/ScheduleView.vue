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
  <div class="px-5 pb-5">
    <div class="flex items-center gap-4 max-[768px]:flex-wrap max-[768px]:justify-between max-[768px]:gap-2">
      <h1 class="mb-0 max-[768px]:w-full">Launch Schedule</h1>
      <div class="flex items-center gap-2 max-[768px]:flex-col max-[768px]:items-start">
        <span v-if="isAdmin && connected" class="badge bg-(--color-success)/85 text-white backdrop-blur-sm">Editing Live</span>
        <span v-else-if="isAdmin" class="badge bg-(--color-warning)/85 text-(--color-warning-text) backdrop-blur-sm">Connecting...</span>
        <span v-else-if="error" class="badge bg-(--color-warning)/85 text-(--color-warning-text) backdrop-blur-sm">{{ error }}</span>
        <span v-else-if="pollLive" class="badge bg-(--color-success)/85 text-white backdrop-blur-sm">Live</span>
        <span v-else class="badge bg-(--color-warning)/85 text-(--color-warning-text) backdrop-blur-sm">Lost Connection</span>
        <span v-if="timerDisplay" class="badge bg-(--color-accent-red)/85 text-white tabular-nums backdrop-blur-sm">{{ timerDisplay }}</span>
      </div>
      <div v-if="isAdmin" class="flex gap-1.5 max-[768px]:flex-col max-[768px]:items-end">
        <button class="timer-btn" @click="startTimer">{{ salvoTimerStarted ? 'Reset' : 'Start' }} Timer</button>
        <button v-if="salvoTimerStarted" class="timer-btn" @click="clearTimer">Clear Timer</button>
      </div>
    </div>

    <div v-if="lanesPerView < lanes.length" class="flex items-center justify-center gap-3 mt-3">
      <button class="lane-arrow prev" :class="{ 'arrow-hot': edgeZone === 'left' && currentLaneIndex > 0 }" :disabled="currentLaneIndex === 0" aria-label="Previous lane" @click="prevLane" />
      <span class="font-semibold text-[0.95rem] text-(--color-text) w-[120px] text-center">{{ lanes[currentLaneIndex]?.label }}</span>
      <button class="lane-arrow next" :class="{ 'arrow-hot': edgeZone === 'right' && currentLaneIndex < maxLaneIndex }" :disabled="currentLaneIndex >= maxLaneIndex" aria-label="Next lane" @click="nextLane" />
    </div>
    <div class="mt-4 flex gap-4 pb-3 items-stretch" :class="{ 'lanes-paginated': lanesPerView < lanes.length }">
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
@reference "tailwindcss";

.badge {
  @apply py-1 px-3 rounded-xl text-xs font-semibold;
  transition: background 0.3s ease, color 0.3s ease;
}

.timer-btn {
  @apply py-1 px-3 border rounded-md text-xs font-semibold cursor-pointer;
  font-family: inherit;
  background: rgba(17, 17, 17, 0.6);
  border-color: rgba(255, 255, 255, 0.15);
  color: #ccc;
  transition: all 0.2s ease;
}
.timer-btn:hover {
  border-color: var(--color-accent-red);
  color: var(--color-accent-red);
  background: rgba(17, 17, 17, 0.8);
}

.lane-arrow {
  @apply w-11 h-[34px] flex items-center justify-center rounded-md cursor-pointer;
  background: rgba(17, 17, 17, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.15);
  color: #ccc;
  transition: all 0.2s ease;
}
.lane-arrow::after {
  content: '';
  @apply block w-[9px] h-[9px] border-solid border-0;
  border-color: currentColor;
}
.lane-arrow.prev::after {
  border-left-width: 2px;
  border-bottom-width: 2px;
  @apply rotate-45 -mr-0.5;
}
.lane-arrow.next::after {
  border-top-width: 2px;
  border-right-width: 2px;
  @apply rotate-45 -ml-0.5;
}
.lane-arrow:disabled {
  @apply opacity-30 cursor-default;
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

.lanes-paginated {
  @apply gap-2 overflow-visible;
}
.lanes-paginated :deep(.lane) {
  @apply hidden flex-1;
}
.lanes-paginated :deep(.lane.lane-visible) {
  @apply flex;
}
</style>
