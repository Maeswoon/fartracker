<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useSiteStatusStore } from '@/stores/site_status'

const store = useSiteStatusStore()
const { data, error, flagColor } = storeToRefs(store)

onMounted(() => store.startPolling())
onUnmounted(() => store.stopPolling())
</script>

<template>
  <div v-if="data" :class="`site-banner banner-${flagColor}`">
    <span class="banner-prefix">Site Status:</span> {{ data.status }}
  </div>
  <div v-else-if="error" class="site-banner banner-error">{{ error }}</div>
</template>

<style scoped>
.site-banner {
  width: 100%;
  padding: 0.5rem 1.5rem;
  text-align: center;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  font-size: 0.95rem;
  color: #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.15);
}

.banner-prefix {
  opacity: 0.85;
  margin-right: 0.25rem;
}

.banner-green  { background-color: #28a745; }
.banner-yellow { background-color: #ffc107; color: #333; }
.banner-red    { background-color: #dc3545; }
.banner-error  { background-color: #555; }
</style>
