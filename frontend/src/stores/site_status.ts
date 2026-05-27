import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getSiteStatus } from '@/api'
import type { SiteStatusResponse } from '@/types'

const POLL_INTERVAL_MS = 10000

export const useSiteStatusStore = defineStore('site_status', () => {
  const data = ref<SiteStatusResponse | null>(null)
  const loading = ref(true)
  const error = ref<string | null>(null)

  let intervalId: ReturnType<typeof setInterval> | null = null
  let subscribers = 0

  const flagColor = computed(() => data.value?.status?.split(' ')[0].toLowerCase() ?? '')
  const localTime = computed(() =>
    data.value?.timestamp ? new Date(data.value.timestamp).toLocaleString() : ''
  )
  const explanation = computed(() => {
    const s = data.value?.status
    if (s === 'Red Flag') return 'We are in a salvo; nobody is allowed to be at the pads unless filling LOX. Please go to a bunker immediately and do not come out until clearance is given over the speakers.'
    if (s === 'Yellow Flag') return 'Only critical launch personnel are allowed at bunkers; all other attendees are not required to be in bunkers. Monitor the PA for a change of status.'
    if (s === 'Green Flag') return 'Pad access is unrestricted for teams and spectators.'
    return ''
  })

  async function fetchStatus() {
    try {
      data.value = await getSiteStatus()
      error.value = null
    } catch {
      error.value = 'Failed to load site status'
    } finally {
      loading.value = false
    }
  }

  function startPolling() {
    subscribers++
    if (intervalId) return
    fetchStatus()
    intervalId = setInterval(fetchStatus, POLL_INTERVAL_MS)
  }

  function stopPolling() {
    subscribers = Math.max(0, subscribers - 1)
    if (subscribers === 0 && intervalId) {
      clearInterval(intervalId)
      intervalId = null
    }
  }

  return { data, loading, error, flagColor, localTime, explanation, startPolling, stopPolling }
})
