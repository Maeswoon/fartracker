<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { RouterLink } from 'vue-router'
import { getSiteStatus, getTeams } from '@/api'
import type { SiteStatusResponse, Team } from '@/types'

const siteStatusData = ref<SiteStatusResponse | null>(null)
const siteStatusLoading = ref(true)
const siteStatusError = ref<string | null>(null)

const flagColor = computed(() => {
  if (!siteStatusData.value?.status) return ''
  return siteStatusData.value.status.split(' ')[0].toLowerCase()
})

const explanation = computed(() => {
  if (!siteStatusData.value?.status) return ''
  if (siteStatusData.value.status === 'Red Flag') {
    return 'We are in a salvo; nobody is allowed to be at the pads unless filling LOX. Please go to a bunker immediately and do not come out until clearance is given over the speakers.'
  } else if (siteStatusData.value.status === 'Yellow Flag') {
    return 'Only critical launch personnel are allowed at bunkers; all other attendees are not required to be in bunkers. Monitor the PA for a change of status.'
  } else {
    return 'Pad access is unrestricted for teams and spectators.'
  }
})

const localTime = computed(() =>
  siteStatusData.value?.timestamp ? new Date(siteStatusData.value.timestamp).toLocaleString() : ''
)

async function fetchStatus() {
  try {
    siteStatusData.value = await getSiteStatus()
    siteStatusLoading.value = false
  } catch {
    siteStatusError.value = 'Failed to load site status'
    siteStatusLoading.value = false
  }
}

const teams = ref<Team[]>([])
const teamsLoading = ref(true)
const teamsError = ref<string | null>(null)

onMounted(async () => {
  fetchStatus()
  siteStatusIntervalId = setInterval(fetchStatus, 10000)

  try {
    teams.value = await getTeams()
  } catch {
    teamsError.value = 'Failed to load teams'
  } finally {
    teamsLoading.value = false
  }
})

let siteStatusIntervalId: ReturnType<typeof setInterval>

onUnmounted(() => clearInterval(siteStatusIntervalId))
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
