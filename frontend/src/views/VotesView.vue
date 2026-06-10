<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { createVote } from '@/api'
import { useVotes } from '@/api/useVotes'
import { useAuthStore } from '@/stores/auth'
import VoteCard from '@/components/VoteCard.vue'
import VoteHistory from '@/components/VoteHistory.vue'

const auth = useAuthStore()
const { votes, connected } = useVotes()
const notifBlocked = ref(false)

onMounted(async () => {
  if (Notification.permission === 'granted') return
  const p = await Notification.requestPermission()
  notifBlocked.value = p === 'denied'
})

const newTitle = ref('')
const durationMinutes = ref(10)
const creating = ref(false)
const createError = ref<string | null>(null)

const activeVotes = computed(() => votes.value.filter(v => v.is_active))
const pastVotes = computed(() => votes.value.filter(v => !v.is_active))

async function doCreate() {
  const title = newTitle.value.trim()
  if (!title) return
  if (!confirm(`Call a vote: "${title}"?`)) return
  creating.value = true
  createError.value = null
  try {
    await createVote(title, durationMinutes.value)
    newTitle.value = ''
  } catch (e: any) {
    createError.value = e?.response?.data?.error || 'Failed to create vote'
  } finally {
    creating.value = false
  }
}
</script>

<template>
  <h1>Votes</h1>

  <div class="votes-layout">
    <section class="votes-create">
      <h2>Call a Vote</h2>
      <form class="create-form" @submit.prevent="doCreate">
        <input
          v-model="newTitle"
          type="text"
          placeholder='e.g. "Delay salvo to 12:30?"'
          maxlength="300"
          class="create-input"
        />
        <div class="create-row">
          <label v-if="auth.user?.is_admin" class="duration-label">
            Duration (min):
            <input v-model.number="durationMinutes" type="number" min="1" max="120" class="duration-input" />
          </label>
          <button type="submit" :disabled="creating || !newTitle.trim()" class="create-btn">
            {{ creating ? 'Creating...' : 'Call Vote' }}
          </button>
        </div>
        <p v-if="createError" class="create-error">{{ createError }}</p>
      </form>
      <p class="ws-status">
        <span class="ws-dot" :class="{ on: connected }" />{{ connected ? 'Live' : 'Disconnected' }}
      </p>
      <p v-if="notifBlocked" class="notif-blocked">
        Notifications are blocked. Enable them in your browser settings to receive vote alerts.
      </p>
    </section>

    <section class="votes-active">
      <h2>Active Votes</h2>
      <div v-if="activeVotes.length === 0" class="empty">No active votes</div>
      <div v-else class="vote-list">
        <VoteCard v-for="vote in activeVotes" :key="vote.id" :vote="vote" />
      </div>
    </section>

    <section class="votes-past">
      <h2>Vote History</h2>
      <VoteHistory :votes="pastVotes" />
    </section>
  </div>
</template>

<style scoped>
@reference "tailwindcss";

.votes-layout {
  @apply flex flex-col gap-6 max-w-3xl mx-auto;
}

/* Create section */
.votes-create {
  @apply rounded-lg border border-(--color-border) bg-(--color-card) p-4;
}
.votes-create h2 {
  @apply m-0 mb-3 text-lg text-(--color-text);
}
.create-form {
  @apply flex flex-col gap-2;
}
.create-input {
  @apply w-full py-2 px-3 rounded border border-(--color-border) bg-(--color-input-bg) text-(--color-text) text-sm;
}
.create-row {
  @apply flex items-center gap-3;
}
.duration-label {
  @apply text-sm text-(--color-text-muted) flex items-center gap-1;
}
.duration-input {
  @apply w-16 py-1 px-2 rounded border border-(--color-border) bg-(--color-input-bg) text-(--color-text) text-sm;
}
.create-btn {
  @apply py-1.5 px-5 rounded border-0 cursor-pointer text-sm font-semibold bg-(--color-accent-red) text-white transition-opacity duration-150;
}
.create-btn:hover:not(:disabled) { @apply opacity-85; }
.create-btn:disabled { @apply opacity-50 cursor-not-allowed; }
.create-error {
  @apply text-sm text-(--color-accent-red-lt) m-0;
}
.ws-status {
  @apply text-xs text-(--color-text-muted) flex items-center gap-1.5 mt-2;
}
.notif-blocked {
  @apply text-base text-(--color-accent-red-lt) font-bold m-0 mt-1;
}
.ws-dot {
  @apply w-2 h-2 rounded-full bg-(--color-toggle-off);
}
.ws-dot.on {
  @apply bg-(--color-success);
}

/* Active votes */
.votes-active h2 {
  @apply m-0 mb-3 text-lg text-(--color-text);
}
.empty {
  @apply text-(--color-text-muted) text-sm;
}
.vote-list {
  @apply flex flex-col gap-3;
}

/* Past votes */
.votes-past h2 {
  @apply m-0 mb-3 text-lg text-(--color-text);
}
</style>
