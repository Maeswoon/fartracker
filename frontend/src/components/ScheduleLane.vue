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
  <div v-if="isSalvo" class="lane salvo-lane">
    <div class="lane-header">
      <span class="lane-label">{{ lane.label }}</span>
      <button v-if="canDrag" class="sort-btn" title="Auto-sort by F2F time" @click="confirmSort">⇅</button>
      <span class="lane-count">{{ lane.teams.length }}</span>
    </div>
    <div class="lane-body slot-grid">
      <div
        v-for="(slotTeams, slotIdx) in slots"
        :key="slotIdx"
        :class="['slot-row', { occupied: slotTeams.length > 0 }]"
      >
        <span class="slot-label">{{ slotIdx * 2 }}m</span>
        <draggable
          v-if="canDrag"
          v-model="slots[slotIdx]"
          :group="{ name: 'schedule', pull: canDrag, put: () => slots[slotIdx].length === 0 }"
          item-key="team_identifier"
          class="slot-drop"
          ghost-class="drop-placeholder"
          :force-fallback="true"
          fallback-class="drag-floating"
          :animation="150"
          :empty-insert-threshold="20"
          :move="(e: any) => checkSlotMove(e, slotIdx)"
          @change="(e: any) => onSlotChange(slotIdx, e)"
        >
          <template #item="{ element: team }">
            <TeamCard :team="team" :lane-label="lane.short_label" draggable :on-update-field="onUpdateField" />
          </template>
        </draggable>
        <div v-else class="slot-drop">
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
      <span class="lane-label">{{ lane.label }}</span>
      <button
        v-if="canDrag && lane.id === 'pending'"
        class="recall-btn"
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
      class="lane-body"
      ghost-class="drop-placeholder"
      drag-class="drag-original"
      :force-fallback="true"
      fallback-class="drag-floating"
      :animation="200"
      @change="onListChange">
      <template #item="{ element: team }">
        <TeamCard
          :team="team"
          :lane-label="lane.short_label"
          draggable
          :on-update-field="onUpdateField" />
      </template>
    </draggable>
    <div v-else class="lane-body">
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
.lane {
  display: flex;
  flex-direction: column;
  flex: 1 1 0;
  min-width: 200px;
  background: var(--color-surface);
  border-radius: 10px;
  border: 1px solid var(--color-border);
  transition: box-shadow 0.3s ease;
}
.lane:hover {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.lane-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: var(--color-nav-bg);
  border-bottom: 1px solid var(--color-border);
  border-radius: 10px 10px 0 0;
  border-radius: 10px 10px 0 0;
}

.lane-label { font-weight: 600; font-size: 0.95rem; color: var(--color-text); }

.sort-btn {
  background: none; border: 1px solid var(--color-border); color: var(--color-text-muted);
  border-radius: 4px; cursor: pointer; font-size: 0.9rem;
  padding: 2px 8px; margin-left: auto; margin-right: 6px;
  transition: all 0.2s ease;
}
.sort-btn:hover { color: var(--color-accent-orange); border-color: var(--color-accent-orange); }

.recall-btn {
  background: none; border: 1px solid var(--color-border); color: var(--color-text-muted);
  border-radius: 4px; cursor: pointer; font-size: 0.85rem;
  padding: 2px 8px; margin-left: auto; margin-right: 6px;
  transition: all 0.2s ease;
}
.recall-btn:hover { color: var(--color-accent-red); border-color: var(--color-accent-red); }

.lane-count {
  background: rgba(192, 57, 43, 0.85); color: #fff;
  border-radius: 10px; padding: 1px 8px; font-size: 0.7rem; font-weight: 600;
  backdrop-filter: blur(4px);
}

.lane-body {
  flex: 1; min-height: 60px; padding: 6px;
  display: flex; flex-direction: column; gap: 4px;
}

/* ── Slot grid ── */
.salvo-lane { min-width: 220px; }
.slot-grid { gap: 0; padding: 2px; overflow-y: auto; }

.slot-row {
  display: flex; align-items: center;
  border-bottom: 1px solid var(--color-border);
  min-height: 24px;
  transition: background 0.15s ease;
}
.slot-row:hover { background: var(--color-table-stripe); }
.slot-row.occupied { min-height: 0; }

.slot-label {
  width: 30px; flex-shrink: 0;
  font-size: 0.7rem; color: var(--color-text-muted);
  text-align: right; padding-right: 4px;
}

.slot-drop {
  flex: 1; min-height: 22px;
  padding: 1px 2px;
}

:deep(.drop-placeholder) { background: var(--color-accent-red); opacity: 0.25; border-radius: 4px; min-height: 30px; transition: opacity 0.15s ease; }
:deep(.drag-original) { opacity: 0.3; }
</style>

<style>
.drag-floating {
  display: none;
}
</style>
