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
  <nav class="flex items-center justify-between px-6 py-2.5 bg-(--color-nav-bg) border-b border-(--color-border) relative z-100 max-[750px]:px-4 max-[750px]:py-2">
    <RouterLink to="/" class="flex items-center gap-2.5 no-underline">
      <img src="/logo.png" alt="" class="h-[30px] w-auto" />
      <span class="font-[Orbitron] text-xl font-bold text-(--color-text) tracking-wider">FAR Tracker</span>
    </RouterLink>
    <button
      class="hamburger"
      :class="{ open }"
      :aria-expanded="open"
      aria-label="Toggle navigation"
      @click="toggle"
    >
      <span /><span /><span />
    </button>
    <div class="flex items-center gap-6 max-[750px]:hidden links-desktop">
      <RouterLink to="/" class="nav-link">Home</RouterLink>
      <RouterLink to="/recovery" class="nav-link">Recovery</RouterLink>
      <RouterLink to="/schedule" class="nav-link">Schedule</RouterLink>
      <template v-if="auth.user?.is_admin">
        <RouterLink to="/frequencies" class="nav-link">Frequencies</RouterLink>
        <RouterLink to="/admin" class="nav-link">Admin</RouterLink>
      </template>
      <button v-if="auth.user" @click="logout" class="desktop-logout-btn bg-transparent border text-(--color-text) text-sm py-1 px-3 rounded cursor-pointer transition duration-200 hover:border-(--color-accent-red-lt) hover:text-(--color-accent-red-lt)">{{ auth.user.username }} // Logout</button>
      <RouterLink v-else to="/login" class="nav-link">Login</RouterLink>
    </div>
    <Transition name="drawer">
      <div v-show="open" class="links-mobile">
        <RouterLink to="/" @click="close" class="mobile-link">Home</RouterLink>
        <RouterLink to="/recovery" @click="close" class="mobile-link">Recovery</RouterLink>
        <RouterLink to="/schedule" @click="close" class="mobile-link">Schedule</RouterLink>
        <template v-if="auth.user?.is_admin">
          <RouterLink to="/frequencies" @click="close" class="mobile-link">Frequencies</RouterLink>
          <RouterLink to="/admin" @click="close" class="mobile-link">Admin</RouterLink>
        </template>
        <button v-if="auth.user" @click="logout" class="mobile-link bg-transparent !border-none text-left"> {{ auth.user.username }} // Logout</button>
        <RouterLink v-else to="/login" @click="close" class="mobile-link">Login</RouterLink>
      </div>
    </Transition>
  </nav>
</template>

<style scoped>
/* desktop nav link underline */
.nav-link {
  color: var(--color-text);
  font-size: 1rem;
  text-decoration: none;
  position: relative;
  transition: color 0.2s ease;
}
.nav-link::after {
  content: '';
  position: absolute;
  bottom: -4px;
  left: 0;
  width: 100%;
  height: 1px;
  background: var(--color-border);
  border-radius: 1px;
  transition: background 0.2s ease, height 0.2s ease;
}
.nav-link:hover::after,
.nav-link.router-link-active::after {
  height: 2px;
  background: var(--color-accent-red);
}
.nav-link:hover,
.nav-link.router-link-active {
  color: var(--color-accent-red-lt);
}

.desktop-logout-btn {
  border-color: var(--color-text-muted) !important;
}

/* hamburger */
.hamburger {
  display: none;
  flex-direction: column;
  justify-content: space-between;
  width: 26px;
  height: 20px;
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
}
.hamburger span {
  display: block;
  height: 2px;
  width: 100%;
  background-color: var(--color-text-muted);
  border-radius: 1px;
  transform-origin: center;
  transition: transform 0.25s ease, opacity 0.2s ease, background-color 0.2s;
}
.hamburger:hover span { background-color: var(--color-accent-red-lt); }
.hamburger.open span:nth-child(1) { transform: translateY(9px) rotate(45deg); }
.hamburger.open span:nth-child(2) { opacity: 0; }
.hamburger.open span:nth-child(3) { transform: translateY(-9px) rotate(-45deg); }

/* mobile drawer */
.links-mobile { display: none; }
@media (max-width: 750px) {
  .hamburger { display: flex; }
  .links-desktop { display: none !important; }
  .links-mobile {
    display: flex;
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    flex-direction: column;
    align-items: stretch;
    gap: 0;
    background: var(--color-nav-bg);
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    padding: 0.5rem 0;
    z-index: 50;
    overflow: hidden;
  }
  .mobile-link {
    padding: 0.75rem 1.25rem;
    border: none;
    border-left: 3px solid transparent;
    border-radius: 0;
    text-align: left;
    font-size: 1rem;
    color: var(--color-text);
    text-decoration: none;
    transition: all 0.2s ease;
  }
  .mobile-link.router-link-active {
    background: rgba(245, 168, 87, 0.12);
    border-left-color: var(--color-accent-red-lt);
    color: var(--color-accent-red-lt);
  }
}

/* drawer transition */
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
