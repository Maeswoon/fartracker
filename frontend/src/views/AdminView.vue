<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getTeamsAbbreviated } from '@/api'
import type { Team } from '@/types'
import SiteStatusForm from '@/components/SiteStatusForm.vue'
import RecoveryPathManager from '@/components/RecoveryPathManager.vue'
import RecoveryPieceManager from '@/components/RecoveryPieceManager.vue'
import TeamStatusForm from '@/components/TeamStatusForm.vue'
import TeamFrequenciesForm from '@/components/TeamFrequenciesForm.vue'
import TeamForm from '@/components/TeamForm.vue'

const teamOptions = ref<Team[]>([])
const pathManagerRef = ref<InstanceType<typeof RecoveryPathManager> | null>(null)

onMounted(async () => {
  try {
    teamOptions.value = await getTeamsAbbreviated()
  } catch {
    console.error('Failed to load teams')
  }
})

async function refreshTeams() {
  try {
    teamOptions.value = await getTeamsAbbreviated()
  } catch {
    console.error('Failed to load teams')
  }
}
</script>

<template>
  <h1>Admin</h1>
  <div class="dashboard-container">
    <SiteStatusForm />
    <RecoveryPathManager ref="pathManagerRef" :teams="teamOptions" />
    <RecoveryPieceManager :teams="teamOptions" @path-added="pathManagerRef?.refresh()" @updated="pathManagerRef?.refresh()" />
    <TeamStatusForm :teams="teamOptions" />
    <TeamFrequenciesForm :teams="teamOptions" />
    <TeamForm :teams="teamOptions" @updated="refreshTeams" />
  </div>
</template>

<style scoped>
@reference "tailwindcss";

.dashboard-container {
  @apply flex flex-row flex-wrap gap-2.5 p-2.5 justify-start;
}

.dashboard-container :deep(.form-card) {
  @apply py-3 px-3.5;
}
.dashboard-container :deep(.form-card:not(.form-card--wide)) {
  @apply max-w-[260px];
}
.dashboard-container :deep(.form-card--wide) {
  @apply max-w-[480px];
}
.dashboard-container :deep(.form-card h3) {
  @apply m-0 mb-2 text-xl p-0 pb-1 border-b-2 border-(--color-accent-red) text-(--color-text);
}
.dashboard-container :deep(.form-card label) {
  @apply mb-0.5;
}
.dashboard-container :deep(.form-card input),
.dashboard-container :deep(.form-card select),
.dashboard-container :deep(.form-card textarea) {
  @apply mb-2 py-1.5 px-2;
}
</style>
