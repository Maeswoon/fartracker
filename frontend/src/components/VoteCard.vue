<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { castBallot } from '@/api'
import { useAuthStore } from '@/stores/auth'
import type { Vote } from '@/types'

const props = defineProps<{ vote: Vote }>()
const emit = defineEmits<{ voted: [] }>()

const auth = useAuthStore()
const busy = ref(false)
const error = ref<string | null>(null)

const now = ref(Date.now())
let timer: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  timer = setInterval(() => { now.value = Date.now() }, 1000)
})
onUnmounted(() => {
  if (timer) clearInterval(timer)
})

const timeLeft = computed(() => {
  const remaining = new Date(props.vote.expires_at).getTime() - now.value
  if (remaining <= 0) return 'Expired'
  const min = Math.floor(remaining / 60000)
  const sec = Math.floor((remaining % 60000) / 1000)
  return `${min}:${sec.toString().padStart(2, '0')}`
})

const userVoted = computed(() =>
  props.vote.ballots.some(b => b.user === auth.user?.username)
)

const totalVotes = computed(() => props.vote.yes_count + props.vote.no_count)
const yesPct = computed(() => totalVotes.value ? Math.round(props.vote.yes_count / totalVotes.value * 100) : 0)
const noPct = computed(() => totalVotes.value ? Math.round(props.vote.no_count / totalVotes.value * 100) : 0)

const resultColor = computed(() => {
  if (props.vote.is_active) return 'var(--color-text-muted)'
  if (!props.vote.quorum_met) return 'var(--color-accent-red-lt)'
  if (props.vote.yes_count > props.vote.no_count) return 'var(--color-success)'
  if (props.vote.no_count > props.vote.yes_count) return 'var(--color-accent-red-lt)'
  return 'var(--color-text-muted)'
})

async function submit(choice: boolean) {
  busy.value = true
  error.value = null
  try {
    await castBallot(props.vote.id, choice)
    emit('voted')
  } catch (e: any) {
    error.value = e?.response?.data?.error || 'Failed to cast ballot'
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="vote-card" :class="{ closed: !vote.is_active }">
    <div class="vote-header">
      <h3 class="vote-title">{{ vote.title }}</h3>
      <span v-if="vote.is_active" class="vote-timer">{{ timeLeft }}</span>
      <span v-else class="vote-badge">Closed</span>
    </div>

    <div class="vote-meta">
      by <strong>{{ vote.created_by }}</strong>
      &middot; {{ vote.eligible_count }} eligible
      &middot; {{ totalVotes }} voted
    </div>

    <div v-if="error" class="vote-error">{{ error }}</div>

    <div v-if="vote.is_active && !userVoted" class="vote-actions">
      <button class="btn-yes" :disabled="busy" @click="submit(true)">Yes</button>
      <button class="btn-no" :disabled="busy" @click="submit(false)">No</button>
    </div>

    <div v-if="userVoted || !vote.is_active" class="vote-results">
      <div class="result-row">
        <span class="result-label">Yes</span>
        <div class="result-bar-track">
          <div class="result-bar result-bar-yes" :style="{ width: yesPct + '%' }" />
        </div>
        <span class="result-count">{{ vote.yes_count }}</span>
      </div>
      <div class="result-row">
        <span class="result-label">No</span>
        <div class="result-bar-track">
          <div class="result-bar result-bar-no" :style="{ width: noPct + '%' }" />
        </div>
        <span class="result-count">{{ vote.no_count }}</span>
      </div>
      <div class="result-outcome" :style="{ color: resultColor }">
        {{ !vote.quorum_met ? '✗ No quorum' : vote.yes_count > vote.no_count ? '✓ Passing' : vote.no_count > vote.yes_count ? '✗ Not passing' : '— Tied' }}
      </div>
    </div>

    <div v-if="userVoted" class="vote-voted-tag">You voted</div>
  </div>
</template>

<style scoped>
@reference "tailwindcss";

.vote-card {
  @apply rounded-lg p-4 border border-(--color-border) bg-(--color-card);
}
.vote-card.closed {
  @apply opacity-75;
}

.vote-header {
  @apply flex justify-between items-start gap-2 mb-1;
}
.vote-title {
  @apply m-0 text-lg text-(--color-text);
}
.vote-timer {
  @apply text-sm font-mono text-(--color-accent-red-lt) whitespace-nowrap;
}
.vote-badge {
  @apply text-xs px-2 py-0.5 rounded bg-(--color-surface-alt) text-(--color-text-muted) whitespace-nowrap;
}

.vote-meta {
  @apply text-sm text-(--color-text-muted) mb-3;
}

.vote-error {
  @apply text-sm text-(--color-accent-red-lt) mb-2;
}

.vote-actions {
  @apply flex gap-2 mb-2;
}
.btn-yes, .btn-no {
  @apply py-1.5 px-5 rounded border-0 cursor-pointer text-sm font-semibold transition-opacity duration-150;
}
.btn-yes:disabled, .btn-no:disabled {
  @apply opacity-50 cursor-not-allowed;
}
.btn-yes { @apply bg-(--color-success) text-white; }
.btn-yes:hover:not(:disabled) { @apply opacity-85; }
.btn-no { @apply bg-(--color-accent-red-lt) text-white; }
.btn-no:hover:not(:disabled) { @apply opacity-85; }

.vote-results {
  @apply flex flex-col gap-1;
}
.result-row {
  @apply flex items-center gap-2;
}
.result-label {
  @apply text-sm text-(--color-text-muted) w-8;
}
.result-bar-track {
  @apply flex-1 h-3 rounded-full bg-(--color-surface-alt) overflow-hidden;
}
.result-bar {
  @apply h-full rounded-full transition-[width] duration-300;
}
.result-bar-yes { @apply bg-(--color-success); }
.result-bar-no { @apply bg-(--color-accent-red-lt); }
.result-count {
  @apply text-sm font-mono text-(--color-text-muted) w-6 text-right;
}
.result-outcome {
  @apply text-sm font-bold mt-1;
}

.vote-voted-tag {
  @apply text-xs text-(--color-text-muted) italic mt-2;
}
</style>
