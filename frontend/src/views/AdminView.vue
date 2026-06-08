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
.dashboard-container {
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  gap: 10px;
  padding: 10px;
  justify-content: flex-start;
}

.dashboard-container :deep(.form-card) {
  padding: 12px 14px;
}

.dashboard-container :deep(.form-card:not(.form-card--wide)) {
  max-width: 260px;
}

.dashboard-container :deep(.form-card--wide) {
  max-width: 480px;
}

.dashboard-container :deep(.form-card h3) {
  margin: 0 0 8px;
  font-size: 1.25rem;
  padding: 0 0 4px 0;
  border-bottom: 2px solid var(--color-accent-red);
  color: var(--color-text);
}

.dashboard-container :deep(.form-card label) {
  margin-bottom: 2px;
}

.dashboard-container :deep(.form-card input),
.dashboard-container :deep(.form-card select),
.dashboard-container :deep(.form-card textarea) {
  margin-bottom: 8px;
  padding: 6px 8px;
}
</style>
