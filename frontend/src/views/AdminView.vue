<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getTeamsAbbreviated, getFrequencies, getTeam, postTeam, patchTeam, postSiteStatus, postTeamStatus, postRecoveryPiece, postRecoveryTrajectory, patchTeamFrequencies } from '@/api'
import type { Team, GpsFrequencies } from '@/types'

const teamOptions = ref<Team[]>([])

onMounted(async () => {
  try {
    teamOptions.value = await getTeamsAbbreviated()
  } catch {
    console.error('Failed to load teams')
  }
})

// Site status form
const selectedSiteStatus = ref('')
const siteStatusSuccess = ref(false)
const siteStatusError = ref<string | null>(null)
const siteStatusOptions = ['Green Flag', 'Yellow Flag', 'Red Flag']

async function submitSiteStatus() {
  siteStatusSuccess.value = false
  siteStatusError.value = null
  try {
    await postSiteStatus(selectedSiteStatus.value)
    siteStatusSuccess.value = true
    selectedSiteStatus.value = ''
  } catch {
    siteStatusError.value = 'Failed to post status.'
  }
}

// Team status form
const selectedTeam = ref('')
const selectedTeamStatus = ref('')
const selectedPadName = ref('')
const teamStatusSuccess = ref(false)
const teamStatusError = ref<string | null>(null)
const teamStatusOptions = ['Absent', 'Onsite', 'At rail', 'In salvo', 'In recovery', 'Recovered']
const padStatuses = ['At rail', 'In salvo']

async function submitTeamStatus() {
  teamStatusSuccess.value = false
  teamStatusError.value = null
  try {
    await postTeamStatus(selectedTeam.value, selectedTeamStatus.value, selectedPadName.value || undefined)
    teamStatusSuccess.value = true
    selectedTeamStatus.value = ''
    selectedPadName.value = ''
  } catch {
    teamStatusError.value = 'Failed to post status.'
  }
}

// Recovery piece form
const pieceTeam = ref('')
const pieceObjectName = ref('')
const pieceLat = ref<number>(0)
const pieceLon = ref<number>(0)
const pieceSuccess = ref(false)
const pieceError = ref<string | null>(null)

async function submitRecoveryPiece() {
  pieceSuccess.value = false
  pieceError.value = null
  if (!pieceTeam.value || !pieceObjectName.value.trim()) {
    pieceError.value = 'Please fill in all fields.'
    return
  }
  try {
    await postRecoveryPiece(pieceTeam.value, pieceObjectName.value, pieceLat.value, pieceLon.value)
    pieceSuccess.value = true
    pieceObjectName.value = ''
    pieceLat.value = 0
    pieceLon.value = 0
  } catch {
    pieceError.value = 'Failed to add recovery piece.'
  }
}

// Frequencies form
const freqTeam = ref('')
const freqFields = ref<GpsFrequencies>({ avionics: '', gse: '', team_comms: '' })
const freqSuccess = ref(false)
const freqError = ref<string | null>(null)

async function loadFrequencies() {
  if (!freqTeam.value) return
  freqError.value = null
  try {
    const all = await getFrequencies()
    const match = all.find(f => f.team_identifier === freqTeam.value)
    const existing: Partial<GpsFrequencies> = match?.gps_frequencies ?? {}
    freqFields.value = {
      avionics: existing.avionics ?? '',
      gse: existing.gse ?? '',
      team_comms: existing.team_comms ?? '',
    }
  } catch {
    freqError.value = 'Failed to load frequencies.'
  }
}

async function submitFrequencies() {
  freqSuccess.value = false
  freqError.value = null
  if (!freqTeam.value) {
    freqError.value = 'Please select a team.'
    return
  }
  try {
    await patchTeamFrequencies(freqTeam.value, freqFields.value)
    freqSuccess.value = true
  } catch {
    freqError.value = 'Failed to update frequencies.'
  }
}

// Recovery trajectory form
const trajTeam = ref('')
const trajLat = ref<number>(0)
const trajLon = ref<number>(0)
const trajSuccess = ref(false)
const trajError = ref<string | null>(null)

async function submitTrajectory() {
  trajSuccess.value = false
  trajError.value = null
  if (!trajTeam.value) {
    trajError.value = 'Please select a team.'
    return
  }
  try {
    await postRecoveryTrajectory(trajTeam.value, trajLat.value, trajLon.value)
    trajSuccess.value = true
    trajLat.value = 0
    trajLon.value = 0
  } catch {
    trajError.value = 'Failed to add trajectory.'
  }
}

// Team create/edit form
const teamFormMode = ref<'new' | 'edit'>('edit')
const teamFormId = ref('')
const teamFormSuccess = ref(false)
const teamFormError = ref<string | null>(null)
const teamFormFields = ref({
  name: '', university: '', team_identifier: '',
  category: '', engine_type: '', fuel_oxidizer: '', target_altitude: '' as string | number,
})
const categoryOptions = [{ value: 'A', label: 'Category A' }, { value: 'B', label: 'Category B' }, { value: 'C', label: 'Category C' }, { value: 'E', label: 'Category Ex' }]
const engineTypeOptions = [{ value: 'H', label: 'Hybrid' }, { value: 'L', label: 'Liquid' }]

function resetTeamForm() {
  teamFormFields.value = { name: '', university: '', team_identifier: '', category: '', engine_type: '', fuel_oxidizer: '', target_altitude: '' }
  teamFormId.value = ''
  teamFormSuccess.value = false
  teamFormError.value = null
}

async function loadTeamForEdit() {
  if (!teamFormId.value) return
  teamFormError.value = null
  try {
    const team = await getTeam(teamFormId.value) as any
    teamFormFields.value = {
      name: team.name ?? '',
      university: team.university ?? '',
      team_identifier: team.team_identifier ?? '',
      category: team.category ?? '',
      engine_type: team.engine_type ?? '',
      fuel_oxidizer: team.fuel_oxidizer ?? '',
      target_altitude: team.target_altitude ?? '',
    }
  } catch {
    teamFormError.value = 'Failed to load team.'
  }
}

async function submitTeamForm() {
  teamFormSuccess.value = false
  teamFormError.value = null
  const payload = {
    ...teamFormFields.value,
    target_altitude: teamFormFields.value.target_altitude !== '' ? Number(teamFormFields.value.target_altitude) : null,
  }
  try {
    if (teamFormMode.value === 'new') {
      await postTeam(payload)
      teamOptions.value = await getTeamsAbbreviated()
      resetTeamForm()
    } else {
      await patchTeam(teamFormId.value, payload)
      teamOptions.value = await getTeamsAbbreviated()
    }
    teamFormSuccess.value = true
  } catch {
    teamFormError.value = teamFormMode.value === 'new' ? 'Failed to create team.' : 'Failed to update team.'
  }
}
</script>

<template>
  <h1>Admin</h1>
  <div class="dashboard-container">

    <div class="form-card">
      <h3>Set Site Status</h3>
      <p v-if="siteStatusSuccess" class="success">Status posted!</p>
      <p v-if="siteStatusError" class="error">{{ siteStatusError }}</p>
      <form @submit.prevent="submitSiteStatus">
        <label>Status</label>
        <select v-model="selectedSiteStatus" required>
          <option value="">Select status:</option>
          <option v-for="s in siteStatusOptions" :key="s" :value="s">{{ s }}</option>
        </select>
        <button type="submit">Post</button>
      </form>
    </div>

    <div class="form-card">
      <h3>Set Team Status</h3>
      <p v-if="teamStatusSuccess" class="success">Status posted!</p>
      <p v-if="teamStatusError" class="error">{{ teamStatusError }}</p>
      <form @submit.prevent="submitTeamStatus">
        <label>Team</label>
        <select v-model="selectedTeam" required>
          <option value="">Select team:</option>
          <option v-for="t in teamOptions" :key="t.team_identifier" :value="t.team_identifier">{{ t.name }}</option>
        </select>
        <label>Status</label>
        <select v-model="selectedTeamStatus" required>
          <option value="">Select status:</option>
          <option v-for="s in teamStatusOptions" :key="s" :value="s">{{ s }}</option>
        </select>
        <template v-if="padStatuses.includes(selectedTeamStatus)">
          <label>Pad Name</label>
          <input v-model="selectedPadName" type="text" placeholder="e.g. Rail 3" />
        </template>
        <button type="submit">Post</button>
      </form>
    </div>

    <div class="form-card">
      <h3>Add Recovery Piece</h3>
      <p v-if="pieceSuccess" class="success">Recovery piece added!</p>
      <p v-if="pieceError" class="error">{{ pieceError }}</p>
      <form @submit.prevent="submitRecoveryPiece">
        <label>Team</label>
        <select v-model="pieceTeam" required>
          <option value="">Select team:</option>
          <option v-for="t in teamOptions" :key="t.team_identifier" :value="t.team_identifier">{{ t.name }}</option>
        </select>
        <label>Object Name</label>
        <input v-model="pieceObjectName" type="text" required />
        <label>Latitude</label>
        <input v-model.number="pieceLat" type="number" step="any" required />
        <label>Longitude</label>
        <input v-model.number="pieceLon" type="number" step="any" required />
        <button type="submit">Submit</button>
      </form>
    </div>

    <div class="form-card">
      <h3>Add Recovery Trajectory</h3>
      <p v-if="trajSuccess" class="success">Trajectory added!</p>
      <p v-if="trajError" class="error">{{ trajError }}</p>
      <form @submit.prevent="submitTrajectory">
        <label>Team</label>
        <select v-model="trajTeam" required>
          <option value="">Select team:</option>
          <option v-for="t in teamOptions" :key="t.team_identifier" :value="t.team_identifier">{{ t.name }}</option>
        </select>
        <label>Latitude</label>
        <input v-model.number="trajLat" type="number" step="any" required />
        <label>Longitude</label>
        <input v-model.number="trajLon" type="number" step="any" required />
        <button type="submit">Submit</button>
      </form>
    </div>

    <div class="form-card form-card--wide">
      <h3>Add / Edit Team</h3>
      <p v-if="teamFormSuccess" class="success">{{ teamFormMode === 'new' ? 'Team created!' : 'Team updated!' }}</p>
      <p v-if="teamFormError" class="error">{{ teamFormError }}</p>
      <div class="mode-toggle">
        <button type="button" :class="{ active: teamFormMode === 'new' }" @click="teamFormMode = 'new'; resetTeamForm()">New Team</button>
        <button type="button" :class="{ active: teamFormMode === 'edit' }" @click="teamFormMode = 'edit'; resetTeamForm()">Edit Team</button>
      </div>
      <form @submit.prevent="submitTeamForm" class="team-form-grid">
        <template v-if="teamFormMode === 'edit'">
          <div class="field-full">
            <label>Team</label>
            <select v-model="teamFormId" required @change="loadTeamForEdit">
              <option value="">Select team:</option>
              <option v-for="t in teamOptions" :key="t.team_identifier" :value="t.team_identifier">{{ t.name }}</option>
            </select>
          </div>
        </template>
        <div>
          <label>Name</label>
          <input v-model="teamFormFields.name" type="text" required />
        </div>
        <div>
          <label>University</label>
          <input v-model="teamFormFields.university" type="text" required />
        </div>
        <template v-if="teamFormMode === 'new'">
          <div>
            <label>Team Identifier</label>
            <input v-model="teamFormFields.team_identifier" type="text" required />
          </div>
        </template>
        <div>
          <label>Category</label>
          <select v-model="teamFormFields.category" required>
            <option value="">Select:</option>
            <option v-for="o in categoryOptions" :key="o.value" :value="o.value">{{ o.label }}</option>
          </select>
        </div>
        <div>
          <label>Engine Type</label>
          <select v-model="teamFormFields.engine_type" required>
            <option value="">Select:</option>
            <option v-for="o in engineTypeOptions" :key="o.value" :value="o.value">{{ o.label }}</option>
          </select>
        </div>
        <div>
          <label>Fuel / Oxidizer</label>
          <input v-model="teamFormFields.fuel_oxidizer" type="text" />
        </div>
        <div>
          <label>Target Altitude (ft)</label>
          <input v-model="teamFormFields.target_altitude" type="number" />
        </div>
        <div class="field-full">
          <button type="submit">{{ teamFormMode === 'new' ? 'Create' : 'Save' }}</button>
        </div>
      </form>
    </div>

    <div class="form-card">
      <h3>Set Team Frequencies</h3>
      <p v-if="freqSuccess" class="success">Frequencies updated!</p>
      <p v-if="freqError" class="error">{{ freqError }}</p>
      <form @submit.prevent="submitFrequencies">
        <label>Team</label>
        <select v-model="freqTeam" required @change="loadFrequencies">
          <option value="">Select team:</option>
          <option v-for="t in teamOptions" :key="t.team_identifier" :value="t.team_identifier">{{ t.name }}</option>
        </select>
        <template v-if="freqTeam">
          <label>Avionics</label>
          <input v-model="freqFields['avionics']" type="text" placeholder="e.g. 433.5 MHz" />
          <label>GSE</label>
          <input v-model="freqFields['gse']" type="text" placeholder="e.g. 915.0 MHz" />
          <label>Team Comms</label>
          <input v-model="freqFields['team_comms']" type="text" placeholder="e.g. 462.5625 MHz" />
          <button type="submit">Save</button>
        </template>
      </form>
    </div>

  </div>
</template>

<style scoped>
.success { color: green; }
.error { color: red; }
.dashboard-container { flex-wrap: wrap; }

.form-card--wide {
  width: 640px;
}

.team-form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 16px;
}

.team-form-grid .field-full {
  grid-column: 1 / -1;
}

.team-form-grid input,
.team-form-grid select {
  width: 100%;
}

.mode-toggle {
  display: flex;
  gap: 8px;
  margin-bottom: 14px;
}
.mode-toggle button {
  flex: 1;
  background-color: #e0e0e0;
  color: var(--color-text-on-light);
  border: 1px solid #ccc;
}
.mode-toggle button.active {
  background-color: var(--color-accent-red);
  color: white;
  border-color: var(--color-accent-red);
}
</style>
