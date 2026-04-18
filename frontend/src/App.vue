<script setup lang="ts">
import { onMounted } from 'vue'
import { RouterView } from 'vue-router'
import AppNavbar from '@/components/AppNavbar.vue'
import AppFooter from '@/components/AppFooter.vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
onMounted(() => auth.restoreSession())
</script>

<template>
  <div class="layout">
    <AppNavbar />
    <main class="content">
      <RouterView />
    </main>
    <AppFooter />
  </div>
</template>

<style scoped>
.layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  width: 100%;
}

.content {
  flex-grow: 1;
  padding: 1rem 2rem;
  width: 100%;
  max-width: 100%;
  overflow-y: auto;
}
</style>
