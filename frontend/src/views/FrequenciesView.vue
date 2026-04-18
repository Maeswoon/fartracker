<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getFrequencies } from '@/api'
import type { Frequency } from '@/types'

const router = useRouter()
const frequencies = ref<Frequency[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

onMounted(async () => {
  try {
    frequencies.value = await getFrequencies()
  } catch (e: any) {
    if (e?.response?.status === 401) {
      router.push({ path: '/login', query: { next: '/frequencies' } })
      return
    }
    error.value = 'Failed to load frequencies'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <h1>Frequencies</h1>
  <div v-if="loading">Loading...</div>
  <div v-else-if="error">{{ error }}</div>
  <div v-else class="table-wrapper">
    <table>
      <thead>
        <tr>
          <th>Team Name</th>
          <th>Avionics</th>
          <th>GSE</th>
          <th>Team Communications</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="freq in frequencies" :key="freq.name">
          <td>{{ freq.name }}</td>
          <td>{{ freq.gps_frequencies['avionics'] }}</td>
          <td>{{ freq.gps_frequencies['gse'] }}</td>
          <td>{{ freq.gps_frequencies['team_comms'] }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
