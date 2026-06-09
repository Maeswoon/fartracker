<script setup lang="ts">
import { computed, onMounted, onUnmounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useSiteStatusStore } from '@/stores/site_status'

const store = useSiteStatusStore()
const { data, error, flagColor } = storeToRefs(store)

const bannerBg: Record<string, string> = {
  green:  'bg-(--color-success)',
  yellow: 'bg-(--color-warning) text-(--color-warning-text)',
  red:    'bg-(--color-accent-red)',
  error:  'bg-(--color-toggle-off)',
}

const bannerClass = computed(() =>
  `w-full text-center font-bold uppercase tracking-wider text-[0.95rem] text-white shadow-sm py-1.5 px-6 max-[600px]:py-2 max-[600px]:px-4 max-[600px]:text-sm ${flagColor.value ? bannerBg[flagColor.value] || '' : ''}`
)

onMounted(() => store.startPolling())
onUnmounted(() => store.stopPolling())
</script>

<template>
  <div v-if="data" :class="[bannerClass, bannerBg[flagColor]]">
    <span class="opacity-85 mr-1">Site Status:</span> {{ data.status }}
  </div>
  <div v-else-if="error" :class="[bannerClass, bannerBg.error]">{{ error }}</div>
</template>
