<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { storeToRefs } from 'pinia'
import { RouterLink } from 'vue-router'
import { getTeams } from '@/api'
import type { Team } from '@/types'
import { useSiteStatusStore } from '@/stores/site_status'

const siteStatus = useSiteStatusStore()
const { data: siteStatusData, loading: siteStatusLoading, error: siteStatusError, flagColor, localTime, explanation } = storeToRefs(siteStatus)

const teams = ref<Team[]>([])
const teamsLoading = ref(true)
const teamsError = ref<string | null>(null)

onMounted(async () => {
  siteStatus.startPolling()
  try {
    teams.value = await getTeams()
  } catch {
    teamsError.value = 'Failed to load teams'
  } finally {
    teamsLoading.value = false
  }
})

onUnmounted(() => siteStatus.stopPolling())
</script>

<template>
  <div class="dashboard-container">
    <div>
      <h3>Current Site Status</h3>
      <div v-if="siteStatusLoading">Loading...</div>
      <div v-else-if="siteStatusError">{{ siteStatusError }}</div>
      <template v-else-if="siteStatusData">
        <div class="center-container">
          <div :class="`status-flag status-${flagColor}`">{{ siteStatusData.status }}</div>
          <br />
          <p>As of {{ localTime }}</p>
        </div>
        <br />
        <div class="center-container">
          <h4>What this means</h4>
          <p>{{ explanation }}</p>
        </div>
      </template>
    </div>

    <div class="table-wrapper">
      <h3>Teams</h3>
      <div v-if="teamsLoading">Loading...</div>
      <div v-else-if="teamsError">{{ teamsError }}</div>
      <table v-else>
        <thead>
          <tr>
            <th>Team Name</th>
            <th>University</th>
            <th>Category</th>
            <th>Engine Type</th>
            <th>Status</th>
          <th>Pad</th>
            <th>More Information</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="team in teams" :key="team.team_identifier">
            <td>{{ team.name }}</td>
            <td>{{ team.university }}</td>
            <td>{{ team.category }}</td>
            <td>{{ team.engine_type_display }}</td>
            <td>{{ team.status }}</td>
          <td>{{ team.pad_name ?? '—' }}</td>
            <td><RouterLink :to="`/teams/${team.team_identifier}`">Full Team Info</RouterLink></td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
