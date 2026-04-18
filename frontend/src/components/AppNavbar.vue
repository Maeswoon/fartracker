<script setup lang="ts">
import { RouterLink, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

function logout() {
  auth.logout()
  router.push('/')
}
</script>

<template>
  <nav>
    <RouterLink to="/" class="brand">FAR Tracker</RouterLink>
    <div class="links">
      <RouterLink to="/">Home</RouterLink>
      <RouterLink to="/frequencies">Frequencies</RouterLink>
      <RouterLink to="/recovery">Recovery</RouterLink>
      <template v-if="auth.user">
        <RouterLink to="/admin">Admin</RouterLink>
        <button @click="logout">Logout</button>
      </template>
      <RouterLink v-else to="/login">Login</RouterLink>
    </div>
  </nav>
</template>

<style scoped>
nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1.5rem;
  background-color: var(--color-nav-bg);
  border-bottom: 1px solid var(--color-nav-border);
}

.brand {
  font-size: 1.5rem;
  font-weight: 700;
  color: white;
  text-decoration: none;
}

.links {
  display: flex;
  gap: 1.5rem;
  align-items: center;
}

.links a {
  color: #ccc;
  font-size: 1rem;
  text-decoration: none;
}

.links a:hover,
.links a.router-link-active {
  color: var(--color-accent-orange-lt);
}

.links button {
  background: none;
  border: 1px solid #ccc;
  color: #ccc;
  font-size: 1rem;
  padding: 0.25rem 0.75rem;
  border-radius: 4px;
  cursor: pointer;
}

.links button:hover {
  border-color: var(--color-accent-orange-lt);
  color: var(--color-accent-orange-lt);
}
</style>
