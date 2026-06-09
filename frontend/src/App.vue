<script setup lang="ts">
import { onMounted } from 'vue'
import { RouterView } from 'vue-router'
import AppNavbar from '@/components/AppNavbar.vue'
import AppFooter from '@/components/AppFooter.vue'
import SiteStatusBanner from '@/components/SiteStatusBanner.vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
onMounted(() => auth.restoreSession())
</script>

<template>
  <div class="layout">
    <AppNavbar />
    <SiteStatusBanner />
    <main class="content">
      <RouterView />
    </main>
    <AppFooter />
  </div>
</template>

<style scoped>
@reference "tailwindcss";

.layout { @apply min-h-screen flex flex-col w-full; }
.content { @apply flex-grow py-4 px-8 w-full max-w-full overflow-y-auto; }
@media (max-width: 600px) {
  .content { @apply py-3 px-4; }
}
</style>
