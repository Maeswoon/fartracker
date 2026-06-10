<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import type { Vote } from '@/types'

defineProps<{ votes: Vote[] }>()

const expanded = ref(new Set<number>())
const visible = ref(new Set<number>())
const isNarrow = ref(false)

let mql: MediaQueryList | null = null
onMounted(() => {
  mql = window.matchMedia('(max-width: 800px)')
  isNarrow.value = mql.matches
  mql.addEventListener('change', e => { isNarrow.value = e.matches })
})
onUnmounted(() => {
  mql?.removeEventListener('change', () => {})
})

function toggle(id: number) {
  if (!isNarrow.value) return
  if (expanded.value.has(id)) {
    // Collapse: remove .open → transition to max-height: 0, then hide
    expanded.value.delete(id)
    setTimeout(() => visible.value.delete(id), 300)
  } else {
    // Expand: show row at max-height: 0, defer .open so transition fires
    visible.value.add(id)
    setTimeout(() => expanded.value.add(id), 0)
  }
}

function formatDate(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleString(undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })
}

function detailDate(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleString(undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit', year: 'numeric' })
}
</script>

<template>
  <div class="vote-history">
    <h3 v-if="votes.length === 0" class="empty-history">No past votes</h3>
    <table v-else class="table-fixed">
      <colgroup>
        <col class="w-[40%] max-[800px]:w-auto">
        <col class="w-[15%] max-[800px]:hidden">
        <col class="w-[20%] max-[800px]:hidden">
        <col class="w-[7%] max-[800px]:hidden">
        <col class="w-[7%] max-[800px]:hidden">
        <col class="w-[11%] max-[800px]:w-[85px]">
      </colgroup>
      <thead>
        <tr>
          <th>Title</th>
          <th class="max-[800px]:hidden">Created by</th>
          <th class="max-[800px]:hidden">Date</th>
          <th class="max-[800px]:hidden">Yes</th>
          <th class="max-[800px]:hidden">No</th>
          <th>Result</th>
        </tr>
      </thead>
      <tbody>
        <template v-for="(vote, index) in votes" :key="vote.id">
          <tr class="vote-row" :class="{ 'row-stripe': index % 2 !== 0 }" @click="toggle(vote.id)">
            <td class="col-title overflow-hidden">
              <span class="chevron" :class="{ open: expanded.has(vote.id) }" />
              {{ vote.title }}
            </td>
            <td class="truncate max-[800px]:hidden">{{ vote.created_by }}</td>
            <td class="truncate max-[800px]:hidden">{{ formatDate(vote.created_at) }}</td>
            <td class="col-num max-[800px]:hidden">{{ vote.yes_count }}</td>
            <td class="col-num max-[800px]:hidden">{{ vote.no_count }}</td>
            <td class="col-result" :class="{
              passed: vote.quorum_met && vote.yes_count > vote.no_count,
              failed: !vote.quorum_met || vote.no_count >= vote.yes_count,
            }">
              {{ !vote.quorum_met ? 'No quorum' : vote.yes_count > vote.no_count ? 'Passed' : vote.no_count > vote.yes_count ? 'Failed' : 'Tied' }}
            </td>
          </tr>
          <tr v-show="visible.has(vote.id)" class="expanded-row" :class="{ open: expanded.has(vote.id) }">
            <td colspan="2">
              <div class="expanded-inner">
                <div class="expanded-detail break-words">
                  <div><strong>By</strong> {{ vote.created_by }}</div>
                  <div><strong>Date</strong> {{ detailDate(vote.created_at) }}</div>
                  <div><strong>Yes</strong> {{ vote.yes_count }} &middot; <strong>No</strong> {{ vote.no_count }}</div>
                </div>
              </div>
            </td>
          </tr>
        </template>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
@reference "tailwindcss";

.vote-history {
  @apply rounded-lg border border-(--color-border) bg-(--color-card) overflow-hidden;
}

table {
  @apply w-full border-collapse;
}

th {
  @apply text-left text-sm text-(--color-text-muted) font-semibold py-2 px-4 bg-(--color-surface-alt) border-b border-(--color-border);
}

td {
  @apply py-2 px-4 text-sm text-(--color-text) border-b border-(--color-border);
}

tr:last-child td {
  @apply border-b-0;
}

.row-stripe td {
  @apply bg-(--color-table-stripe);
}

@media (max-width: 800px) {
  .vote-row {
    @apply cursor-pointer;
  }
}
.vote-row:hover td {
  @apply bg-(--color-surface-alt);
}

.chevron {
  display: none;
  width: 0;
  height: 0;
  border-left: 5px solid transparent;
  border-right: 5px solid transparent;
  border-top: 6px solid var(--color-text-muted);
  transition: transform 0.25s ease;
  vertical-align: middle;
  margin-right: 6px;
  margin-bottom: 1px;
}
.chevron.open {
  transform: rotate(180deg);
}
@media (max-width: 800px) {
  .chevron {
    display: inline-block;
  }
}

.col-title {
  @apply font-medium;
}
.col-num {
  @apply font-mono text-right;
}
.col-result.passed {
  @apply font-semibold text-(--color-success);
}
.col-result.failed {
  @apply font-semibold text-(--color-accent-red-lt);
}

.expanded-row td {
  @apply py-0 border-b-0 bg-(--color-surface);
}
.expanded-inner {
  max-height: 0;
  overflow: hidden;
  transition: max-height 0.3s ease;
}
.expanded-row.open .expanded-inner {
  max-height: 100px;
}
.expanded-detail {
  @apply flex flex-col gap-0.5 text-xs text-(--color-text-muted) py-2 px-4;
}

.empty-history {
  @apply text-center text-(--color-text-muted) py-6 m-0;
}
</style>
