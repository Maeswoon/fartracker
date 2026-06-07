import { ref, watch, onUnmounted, type Ref } from 'vue'
import * as Y from 'yjs'
import { WebsocketProvider } from 'y-websocket'
import { getScheduleWsUrl } from '@/config'
import { getSchedule, getCurrentUser } from '@/api'
import { router } from '@/router'
import type { ScheduleLane, ScheduleTeam } from '@/types'

function assembleLanes(
  laneDefs: { id: string; label: string; short_label: string }[],
  laneTeams: Record<string, string[]>,
  teamDataOverrides: Record<string, Record<string, number>>,
  teams: ScheduleTeam[],
): { lanes: ScheduleLane[]; teamMap: Map<string, ScheduleTeam> } {
  const teamMap = new Map<string, ScheduleTeam>()
  for (const t of teams) {
    const overrides = teamDataOverrides[t.team_identifier] || {}
    teamMap.set(t.team_identifier, {
      ...t,
      fill_to_fire: overrides.fill_to_fire ?? t.fill_to_fire,
      hold_time: overrides.hold_time ?? t.hold_time,
      salvo_time: overrides.salvo_time ?? t.salvo_time,
    })
  }

  const placedIds = new Set<string>()
  const lanes: ScheduleLane[] = laneDefs.map(ld => {
    const teamIds = (laneTeams[ld.id] || []).filter(tid => teamMap.has(tid))
    teamIds.forEach(tid => placedIds.add(tid))
    let laneTeamsArr = teamIds.map(tid => teamMap.get(tid)!)
    if (ld.id.startsWith('salvo')) {
      laneTeamsArr = [...laneTeamsArr].sort((a, b) => a.salvo_time - b.salvo_time)
    }
    return { id: ld.id, label: ld.label, short_label: ld.short_label, teams: laneTeamsArr }
  })

  const unplaced = [...teamMap.keys()].filter(tid => !placedIds.has(tid))
  if (unplaced.length) {
    const pending = lanes.find(l => l.id === 'pending')
    if (pending) pending.teams.push(...unplaced.map(tid => teamMap.get(tid)!))
  }

  return { lanes, teamMap }
}

export function useSchedule(isAdmin: Ref<boolean>) {
  const lanes = ref<ScheduleLane[]>([])
  const teamMap = ref<Map<string, ScheduleTeam>>(new Map())
  const connected = ref(false)
  const lastUpdate = ref<number | null>(null)
  const salvoTimerStarted = ref<string | null>(null)
  const error = ref<string | null>(null)

  let ydoc: Y.Doc | null = null
  let provider: WebsocketProvider | null = null
  let pollInterval: ReturnType<typeof setInterval> | null = null
  let laneDefs: { id: string; label: string; short_label: string }[] = []

  // -- Yjs-derived helpers --------------------------------------------------

  function rebuildLanes() {
    if (!ydoc) return
    const yTeams = ydoc.getMap('teams')
    const yLanes = ydoc.getMap('lanes')

    const meta: Record<string, Record<string, number>> = {}
    yTeams.forEach((val, key) => {
      if (val instanceof Y.Map) {
        const m: Record<string, number> = {}
        val.forEach((v, k) => { m[k as string] = v as number })
        meta[key as string] = m
      }
    })

    const laneTeams: Record<string, string[]> = {}
    yLanes.forEach((val, key) => {
      if (val instanceof Y.Array) {
        laneTeams[key as string] = val.toArray() as string[]
      }
    })

    const baseTeams = [...teamMap.value.values()].map(t => ({ ...t }))
    const { lanes: newLanes, teamMap: newMap } = assembleLanes(laneDefs, laneTeams, meta, baseTeams)
    lanes.value = newLanes
    teamMap.value = newMap
    lastUpdate.value = Date.now()
  }

  function getTeamMeta(teamId: string): Y.Map<any> {
    const yTeams = ydoc!.getMap('teams')
    let m = yTeams.get(teamId) as Y.Map<any> | undefined
    if (!m) {
      m = new Y.Map()
      const base = teamMap.value.get(teamId)
      if (base) {
        m.set('fill_to_fire', base.fill_to_fire)
        m.set('hold_time', base.hold_time)
        m.set('salvo_time', base.salvo_time)
        m.set('lane', lanes.value.find(l => l.teams.some(t => t.team_identifier === teamId))?.id || 'pending')
      }
      yTeams.set(teamId, m)
    }
    return m
  }

  // -- Yjs setup ------------------------------------------------------------

  function initYjs() {
    ydoc = new Y.Doc()
    provider = new WebsocketProvider(getScheduleWsUrl(), 'schedule', ydoc)

    provider.on('status', (event: { status: string }) => {
      connected.value = event.status === 'connected'
    })

    provider.on('connection-close', async (event: CloseEvent | null) => {
      if (event?.code === 4001) {
        provider?.disconnect()
        try {
          await getCurrentUser()
          provider?.connect()
        } catch {
          router.push('/login')
        }
      }
    })

    let rebuildTimeout: ReturnType<typeof setTimeout> | null = null
    ydoc.on('update', () => {
      if (rebuildTimeout) clearTimeout(rebuildTimeout)
      rebuildTimeout = setTimeout(rebuildLanes, 50)
    })
  }

  // -- Polling (non-admins) -------------------------------------------------

  function initPolling() {
    async function fullPoll() {
      try {
        const resp = await getSchedule()
        laneDefs = resp.lane_definitions
        const { lanes: newLanes, teamMap: newMap } = assembleLanes(
          resp.lane_definitions, resp.lane_teams, resp.team_data, resp.teams,
        )
        lanes.value = newLanes
        teamMap.value = newMap
        salvoTimerStarted.value = resp.salvo_timer_started
        lastUpdate.value = Date.now()
        error.value = null
      } catch {
        error.value = 'Failed to load schedule'
      }
    }
    fullPoll()
    pollInterval = setInterval(fullPoll, 10_000)
  }

  // -- Start / restart ------------------------------------------------------

  async function fetchLaneDefs() {
    try {
      const resp = await getSchedule()
      laneDefs = resp.lane_definitions
      const { lanes: newLanes, teamMap: newMap } = assembleLanes(
        resp.lane_definitions, resp.lane_teams, resp.team_data, resp.teams,
      )
      lanes.value = newLanes
      teamMap.value = newMap
      salvoTimerStarted.value = resp.salvo_timer_started
      lastUpdate.value = Date.now()
      return resp
    } catch {
      error.value = 'Failed to load schedule'
      return null
    }
  }

  async function start() {
    const resp = await fetchLaneDefs()
    if (!resp) return
    if (isAdmin.value) {
      try {
        await getCurrentUser()
      } catch {
        router.push('/login')
        return
      }
      initYjs()
    } else {
      initPolling()
    }
  }

  // -- Lane helpers (for drag-and-drop) -------------------------------------

  function ensureLane(laneId: string): Y.Array<string> {
    const yLanes = ydoc!.getMap('lanes')
    let arr = yLanes.get(laneId) as Y.Array<string> | undefined
    if (!arr) {
      const currentLane = lanes.value.find(l => l.id === laneId)
      const teamIds = currentLane ? currentLane.teams.map(t => t.team_identifier) : []
      arr = new Y.Array<string>()
      if (teamIds.length > 0) arr.insert(0, teamIds)
      yLanes.set(laneId, arr)
    }
    return arr
  }

  function moveTeam(teamId: string, fromLaneId: string, toLaneId: string, toIndex: number) {
    const team = teamMap.value.get(teamId)
    if (!team) return

    const newLanes = lanes.value.map(l => ({
      ...l,
      teams: l.teams.filter(t => t.team_identifier !== teamId),
    }))
    const dstLane = newLanes.find(l => l.id === toLaneId)
    if (dstLane) {
      const existingIdx = dstLane.teams.findIndex(t => t.team_identifier === teamId)
      if (existingIdx >= 0) dstLane.teams.splice(existingIdx, 1)
      dstLane.teams.splice(Math.min(toIndex, dstLane.teams.length), 0, team)
    }
    lanes.value = newLanes

    if (!ydoc) return

    getTeamMeta(teamId).set('lane', toLaneId)

    if (fromLaneId) {
      const srcArr = ensureLane(fromLaneId)
      const idx = srcArr.toArray().indexOf(teamId)
      if (idx >= 0) srcArr.delete(idx, 1)
    }
    const dstArr = ensureLane(toLaneId)
    const current = dstArr.toArray()
    const existingIdx = current.indexOf(teamId)
    if (existingIdx >= 0) {
      dstArr.delete(existingIdx, 1)
      const adjustedIdx = existingIdx < toIndex ? toIndex - 1 : toIndex
      dstArr.insert(adjustedIdx, [teamId])
    } else {
      dstArr.insert(Math.min(toIndex, dstArr.length), [teamId])
    }

    if (toLaneId === 'pending') {
      updateTeamField(teamId, 'salvo_time', 0)
    }
  }

  function recallAll() {
    const others = lanes.value.filter(l => l.id !== 'pending')
    const toRecall: { teamId: string; fromLaneId: string }[] = []
    for (const lane of others) {
      for (const t of lane.teams) {
        toRecall.push({ teamId: t.team_identifier, fromLaneId: lane.id })
      }
    }
    if (toRecall.length === 0) return

    lanes.value = lanes.value.map(l => ({
      ...l,
      teams: l.id === 'pending'
        ? [...l.teams, ...toRecall.map(r => teamMap.value.get(r.teamId)).filter(Boolean) as ScheduleTeam[]]
        : [],
    }))

    if (!ydoc) return
    const pendingArr = ensureLane('pending')
    const currentPending = pendingArr.toArray()

    for (const { teamId, fromLaneId } of toRecall) {
      getTeamMeta(teamId).set('lane', 'pending')
      getTeamMeta(teamId).set('salvo_time', 0)
      const tm = teamMap.value.get(teamId)
      if (tm) tm.salvo_time = 0
      if (fromLaneId) {
        const srcArr = ensureLane(fromLaneId)
        const idx = srcArr.toArray().indexOf(teamId)
        if (idx >= 0) srcArr.delete(idx, 1)
      }
      if (!currentPending.includes(teamId)) {
        pendingArr.push([teamId])
      }
    }
  }

  function updateTeamField(teamId: string, field: string, value: number) {
    const existing = teamMap.value.get(teamId)
    if (existing) {
      (existing as any)[field] = value
      lanes.value = lanes.value.map(l => ({ ...l, teams: [...l.teams] }))
    }
    if (ydoc) {
      getTeamMeta(teamId).set(field, value)
    }
  }

  // -- Lifecycle ------------------------------------------------------------

  watch(isAdmin, () => {
    if (pollInterval) { clearInterval(pollInterval); pollInterval = null }
    if (provider) { provider.destroy(); provider = null }
    if (ydoc) { ydoc.destroy(); ydoc = null }
    start()
  }, { immediate: true })

  onUnmounted(() => {
    if (pollInterval) clearInterval(pollInterval)
    if (provider) provider.destroy()
    if (ydoc) ydoc.destroy()
  })

  return { lanes, teamMap, connected, lastUpdate, salvoTimerStarted, error, moveTeam, recallAll, updateTeamField, start }
}
