<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import draggable from 'vuedraggable'
import type { ScheduleLane, ScheduleTeam } from '@/types'
import { useAuthStore } from '@/stores/auth'
import TeamCard from './TeamCard.vue'

const props = defineProps<{
  lane: ScheduleLane
  draggable: boolean
  onUpdateField: (teamId: string, field: string, value: number) => void
  teamMinSlots: Map<string, number>  // teamId → minimum slot index
}>()

const emit = defineEmits<{
  change: [payload: { teamId: string; toIndex: number }]
  autoSort: []
  recallAll: []
  dragStart: []
  dragEnd: []
}>()

const auth = useAuthStore()
const canDrag = computed(() => props.draggable && !!auth.user?.is_admin)
const isSalvo = computed(() => props.lane.id.startsWith('salvo'))

const SLOT_COUNT = 26

// For salvo lanes: one array per slot, each with 0 or 1 teams
const slots = ref<ScheduleTeam[][]>(
  Array.from({ length: SLOT_COUNT }, () => [])
)

function syncSlots() {
  const bySlot: ScheduleTeam[][] = Array.from({ length: SLOT_COUNT }, () => [])
  for (const t of props.lane.teams) {
    const idx = t.salvo_time
    if (idx >= 0 && idx < SLOT_COUNT) {
      bySlot[idx].push(t)
    }
  }
  slots.value = bySlot
}
watch(() => props.lane.teams, syncSlots, { deep: true, immediate: true })

// Non-salvo lane list
const list = ref<ScheduleTeam[]>([...props.lane.teams])
watch(() => props.lane.teams, (val) => { list.value = [...val] }, { deep: true })

function onSlotChange(slotIdx: number, event: any) {
  if (event.added) {
    const team = event.added.element as ScheduleTeam
    const minSlot = Math.ceil(team.fill_to_fire / 2)
    const actualSlot = Math.max(slotIdx, minSlot)
    emit('change', { teamId: team.team_identifier, toIndex: actualSlot })
  } else if (event.moved) {
    emit('change', {
      teamId: event.moved.element.team_identifier,
      toIndex: event.moved.newIndex,
    })
  }
}

function checkSlotMove(evt: any, slotIdx: number): boolean {
  const teamId = evt.dragged?.dataset?.id
  if (!teamId) return true
  const minSlot = props.teamMinSlots.get(teamId) ?? 0
  return slotIdx >= minSlot
}

function onListChange(event: any) {
  if (event.added) {
    emit('change', {
      teamId: event.added.element.team_identifier,
      toIndex: event.added.newIndex,
    })
  } else if (event.moved) {
    emit('change', {
      teamId: event.moved.element.team_identifier,
      toIndex: event.moved.newIndex,
    })
  }
}

function confirmSort() {
  if (window.confirm(`Auto-sort ${props.lane.label} by fill-to-fire time?`)) {
    emit('autoSort')
  }
}

function confirmRecall() {
  if (window.confirm('Move all teams from other lanes back to Pending?')) {
    emit('recallAll')
  }
}
</script>

<template>
  <!-- ── Salvo lane: fixed slot grid ── -->
  <div v-if="isSalvo" class="lane min-w-[220px]">
    <div class="lane-header">
      <span class="font-semibold text-[0.95rem] text-(--color-text)">{{ lane.label }}</span>
      <button v-if="canDrag" class="lane-btn sort-btn" title="Auto-sort by F2F time" @click="confirmSort">⇅</button>
      <span class="lane-count">{{ lane.teams.length }}</span>
    </div>
    <div class="flex-1 min-h-[60px] p-0.5 flex flex-col gap-0 overflow-y-auto">
      <div
        v-for="(slotTeams, slotIdx) in slots"
        :key="slotIdx"
        :class="['slot-row', { 'min-h-0': slotTeams.length > 0 }]"
      >
        <span class="w-[30px] shrink-0 text-[0.7rem] text-(--color-text-muted) text-right pr-1">{{ slotIdx * 2 }}m</span>
        <draggable
          v-if="canDrag"
          v-model="slots[slotIdx]"
          :group="{ name: 'schedule', pull: canDrag, put: () => slots[slotIdx].length === 0 }"
          item-key="team_identifier"
          class="flex-1 min-h-[22px] py-px px-0.5"
          ghost-class="drop-placeholder"
          :force-fallback="true"
          fallback-class="drag-floating"
          :animation="150"
          :empty-insert-threshold="20"
          :move="(e: any) => checkSlotMove(e, slotIdx)"
          @change="(e: any) => onSlotChange(slotIdx, e)"
          @start="() => emit('dragStart')"
          @end="() => emit('dragEnd')"
        >
          <template #item="{ element: team }">
            <TeamCard :team="team" :lane-label="lane.short_label" draggable :on-update-field="onUpdateField" />
          </template>
        </draggable>
        <div v-else class="flex-1 min-h-[22px] py-px px-0.5">
          <TeamCard
            v-for="team in slotTeams"
            :key="team.team_identifier"
            :team="team"
            :lane-label="lane.short_label"
            :on-update-field="onUpdateField"
          />
        </div>
      </div>
    </div>
  </div>

  <!-- ── Pending / Recovered ── -->
  <div v-else class="lane">
    <div class="lane-header">
      <span class="font-semibold text-[0.95rem] text-(--color-text)">{{ lane.label }}</span>
      <button
        v-if="canDrag && lane.id === 'pending'"
        class="lane-btn recall-btn"
        title="Move all teams back to Pending"
        @click="confirmRecall"
      >↺ Recall</button>
      <span class="lane-count">{{ lane.teams.length }}</span>
    </div>
    <draggable
      v-if="canDrag"
      v-model="list"
      :group="{ name: 'schedule', pull: canDrag, put: true }"
      item-key="team_identifier"
      class="flex-1 min-h-[60px] p-1.5 flex flex-col gap-1"
      ghost-class="drop-placeholder"
      drag-class="drag-original"
      :force-fallback="true"
      fallback-class="drag-floating"
      :animation="200"
      @change="onListChange"
      @start="() => emit('dragStart')"
      @end="() => emit('dragEnd')">
      <template #item="{ element: team }">
        <TeamCard
          :team="team"
          :lane-label="lane.short_label"
          draggable
          :on-update-field="onUpdateField" />
      </template>
    </draggable>
    <div v-else class="flex-1 min-h-[60px] p-1.5 flex flex-col gap-1">
      <TeamCard
        v-for="team in list"
        :key="team.team_identifier"
        :team="team"
        :lane-label="lane.short_label"
        :on-update-field="onUpdateField" />
    </div>
  </div>
</template>

<style scoped>
@reference "tailwindcss";

.lane {
  @apply flex flex-col flex-1 min-w-[200px] rounded-[10px] border border-(--color-border);
  background: var(--color-surface);
  transition: box-shadow 0.3s ease;
}
.lane:hover {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.lane-header {
  @apply flex justify-between items-center py-2 px-3 rounded-t-[10px];
  background: var(--color-nav-bg);
  border-bottom: 1px solid var(--color-border);
}

.lane-btn {
  @apply bg-transparent border border-(--color-border) text-(--color-text-muted) rounded cursor-pointer ml-auto mr-1.5 transition-all duration-200;
}
.lane-btn:hover {
  color: var(--color-accent-red);
  border-color: var(--color-accent-red);
}
.sort-btn { font-size: 0.9rem; padding: 2px 8px; }
.recall-btn { font-size: 0.85rem; padding: 2px 8px; }

.lane-count {
  @apply rounded-[10px] py-px px-2 text-[0.7rem] font-semibold text-white;
  background: color-mix(in srgb, var(--color-accent-red) 85%, transparent);
  backdrop-filter: blur(4px);
}

.slot-row {
  @apply flex items-center border-b border-(--color-border) min-h-[24px];
  transition: background 0.15s ease;
}
.slot-row:hover { background: var(--color-table-stripe); }

:deep(.drop-placeholder) {
  @apply rounded min-h-[30px];
  background: var(--color-accent-red);
  opacity: 0.25;
  transition: opacity 0.15s ease;
}
:deep(.drag-original) { opacity: 0.3; }
</style>

<style>
.drag-floating {
  display: none;
}
</style>
