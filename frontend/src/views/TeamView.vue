<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getTeam, getTeamStatuses } from '@/api'
import type { TeamDetailed, TeamStatus } from '@/types'

const route = useRoute()
const teamId = route.params.teamId as string

const team = ref<TeamDetailed | null>(null)
const statuses = ref<TeamStatus[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

onMounted(async () => {
  if (!teamId || teamId.includes('assets')) return
  try {
    ;[team.value, statuses.value] = await Promise.all([
      getTeam(teamId),
      getTeamStatuses(teamId),
    ])
  } catch {
    error.value = 'Failed to load team data'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div v-if="loading">Loading...</div>
  <div v-else-if="error">{{ error }}</div>
  <template v-else>
    <div class="table-wrapper">
      <h3>Team Details</h3>
      <table v-if="team">
        <tbody>
          <tr><td>Team Name</td><td>{{ team.name }}</td></tr>
          <tr><td>University</td><td>{{ team.university }}</td></tr>
          <tr><td>Category</td><td>{{ team.category }}</td></tr>
          <tr><td>Engine Type</td><td>{{ team.engine_type_display }}</td></tr>
          <tr><td>Fuel and Oxidizer</td><td>{{ team.fuel_oxidizer }}</td></tr>
          <tr><td>Pad Name</td><td>{{ statuses[0]?.pad_name ?? '—' }}</td></tr>

          <tr><td>Target Altitude</td><td>{{ (team as any).target_altitude != null ? `${(team as any).target_altitude.toLocaleString()} ft` : '—' }}</td></tr>
        </tbody>
      </table>
    </div>

    <div class="table-wrapper">
      <h3>Team Statuses</h3>
      <table>
        <thead>
          <tr>
            <th>Status</th>
            <th>Timestamp</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(s, i) in statuses" :key="s.id" :style="i === 0 ? { fontWeight: 'bold' } : {}">
            <td>{{ s.status }}</td>
            <td>{{ s.timestamp }}</td>
          </tr>
        </tbody>
      </table>
    </div>

  </template>
</template>
