import { ref, onUnmounted } from 'vue'
import { getWsBaseUrl } from '@/config'
import { getVotes } from '@/api'
import type { Vote } from '@/types'

function voteResult(v: Vote): string {
  if (!v.quorum_met) return 'No quorum'
  if (v.yes_count > v.no_count) return 'Passed'
  if (v.no_count > v.yes_count) return 'Failed'
  return 'Tied'
}

function notify(title: string, body: string) {
  if (Notification.permission !== 'granted') return
  new Notification(title, { body, icon: '/logo.png' })
}

export function useVotes() {
  const votes = ref<Vote[]>([])
  const connected = ref(false)
  const error = ref<string | null>(null)

  let ws: WebSocket | null = null
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null
  let mounted = true

  function connect() {
    if (!mounted) return
    ws = new WebSocket(`${getWsBaseUrl()}votes/`)

    ws.onopen = () => {
      connected.value = true
      error.value = null
    }

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        if (msg.type === 'update') {
          const updated = msg.vote as Vote
          const idx = votes.value.findIndex(v => v.id === updated.id)
          if (idx >= 0) {
            const prev = votes.value[idx]
            votes.value[idx] = updated
            // Vote just closed
            if (prev.is_active && !updated.is_active) {
              notify('Vote Closed', `"${updated.title}" — ${voteResult(updated)}`)
            }
          } else {
            votes.value.unshift(updated)
            // New vote created
            notify('New Vote Called', updated.title)
          }
          votes.value = [...votes.value]
        }
      } catch {
        // ignore parse errors
      }
    }

    ws.onclose = (event) => {
      connected.value = false
      ws = null
      if (!mounted) return
      if (event?.code === 4001) return
      reconnectTimer = setTimeout(connect, 3000)
    }

    ws.onerror = () => {}
  }

  async function refresh() {
    try {
      const data = await getVotes()
      votes.value = data
    } catch {
      error.value = 'Failed to load votes'
    }
  }

  refresh().then(() => connect())

  onUnmounted(() => {
    mounted = false
    if (reconnectTimer) clearTimeout(reconnectTimer)
    if (ws) {
      ws.onclose = null
      ws.close()
      ws = null
    }
  })

  return { votes, connected, error, refresh }
}
