<script setup lang="ts">
import { ref, watch } from 'vue'
import { RouterLink, useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const open = ref(false)
const toggle = () => { open.value = !open.value }
const close = () => { open.value = false }

watch(() => route.fullPath, close)

function logout() {
  auth.logout()
  close()
  router.push('/')
}
</script>

<template>
  <nav>
    <RouterLink to="/" class="brand">FAR Tracker</RouterLink>
    <button
      class="hamburger"
      :class="{ open }"
      :aria-expanded="open"
      aria-label="Toggle navigation"
      @click="toggle"
    >
      <span /><span /><span />
    </button>
    <div class="links links-desktop">
      <RouterLink to="/">Home</RouterLink>
      <RouterLink to="/recovery">Recovery</RouterLink>
      <template v-if="auth.user?.is_admin">
        <RouterLink to="/frequencies">Frequencies</RouterLink>
        <RouterLink to="/admin">Admin</RouterLink>
      </template>
      <button v-if="auth.user" @click="logout">Logout</button>
      <RouterLink v-else to="/login">Login</RouterLink>
    </div>
    <Transition name="drawer">
      <div v-show="open" class="links links-mobile">
        <RouterLink to="/" @click="close">Home</RouterLink>
        <RouterLink to="/recovery" @click="close">Recovery</RouterLink>
        <template v-if="auth.user?.is_admin">
          <RouterLink to="/frequencies" @click="close">Frequencies</RouterLink>
          <RouterLink to="/admin" @click="close">Admin</RouterLink>
        </template>
        <button v-if="auth.user" @click="logout">Logout</button>
        <RouterLink v-else to="/login" @click="close">Login</RouterLink>
      </div>
    </Transition>
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
  position: relative;
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

.hamburger {
  display: none;
  flex-direction: column;
  justify-content: space-between;
  width: 28px;
  height: 22px;
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
}

.hamburger span {
  display: block;
  height: 3px;
  width: 100%;
  background-color: #ccc;
  border-radius: 2px;
  transform-origin: center;
  transition: transform 0.25s ease, opacity 0.2s ease, background-color 0.2s;
}

.hamburger:hover span { background-color: var(--color-accent-orange-lt); }

.hamburger.open span:nth-child(1) { transform: translateY(9.5px) rotate(45deg); }
.hamburger.open span:nth-child(2) { opacity: 0; }
.hamburger.open span:nth-child(3) { transform: translateY(-9.5px) rotate(-45deg); }

.links-mobile { display: none; }

@media (max-width: 600px) {
  nav { padding: 0.6rem 1rem; }

  .hamburger { display: flex; }
  .links-desktop { display: none; }

  .links-mobile {
    display: flex;
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    flex-direction: column;
    align-items: stretch;
    gap: 0;
    background-color: var(--color-nav-bg);
    border-bottom: 1px solid var(--color-nav-border);
    padding: 0.5rem 0;
    z-index: 50;
    overflow: hidden;
  }

  .links-mobile a,
  .links-mobile button {
    padding: 0.75rem 1.25rem;
    border: none;
    border-left: 3px solid transparent;
    border-radius: 0;
    text-align: left;
    transition: background-color 0.15s ease, border-color 0.15s ease, color 0.15s ease;
  }

  .links-mobile a.router-link-active {
    background-color: rgba(245, 168, 87, 0.12);
    border-left-color: var(--color-accent-orange-lt);
    color: var(--color-accent-orange-lt);
  }

  .links-mobile button {
    background: none;
    text-align: left;
    font-size: 1rem;
  }
}

.drawer-enter-active,
.drawer-leave-active {
  transition: max-height 0.25s ease, opacity 0.2s ease;
  overflow: hidden;
}

.drawer-enter-from,
.drawer-leave-to {
  max-height: 0;
  opacity: 0;
}

.drawer-enter-to,
.drawer-leave-from {
  max-height: 400px;
  opacity: 1;
}
</style>
