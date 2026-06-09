<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const username = ref('')
const password = ref('')
const error = ref<string | null>(null)
const loggedIn = ref(false)

const origin = window.location.origin

const next = computed(() => {
  const n = route.query.next
  return typeof n === 'string' && n.startsWith('/') ? n : '/'
})
const nextLabel = computed(() => {
  if (next.value === '/') return 'Home'
  return next.value
})

async function handleSubmit() {
  error.value = null
  try {
    await auth.login(username.value, password.value)
    loggedIn.value = true
  } catch {
    error.value = 'Login failed. Please check your credentials.'
  }
}

const copied = ref(false)

function copyToken() {
  if (!auth.refreshToken) return
  navigator.clipboard.writeText(auth.refreshToken)
  copied.value = true
  setTimeout(() => copied.value = false, 2000)
}

function proceed() {
  router.push(next.value)
}
</script>

<template>
  <div class="flex justify-center py-12 px-4">
    <div v-if="loggedIn" class="form-card" style="max-width: 600px">
      <h2>API Access</h2>
      <p class="muted">
        Refresh token (expires in 7 days):
      </p>
      <pre class="token-box">{{ auth.refreshToken }}</pre>
      <button class="mb-4 text-sm py-1.5 px-3" @click="copyToken">{{ copied ? 'Copied!' : 'Copy to clipboard' }}</button>
      <p class="muted">
        Use it to get an access token (valid for 1 hour):<br/>
        <code>curl -X POST {{ origin }}/api/token/refresh/ -H 'Content-Type: application/json' -d '{"refresh": "&lt;token&gt;"}'</code>
      </p>
      <p class="text-(--color-accent-red)">Store this token securely. Do not share it.</p>
      <button @click="proceed">Continue to {{ nextLabel }}</button>
    </div>
    <div v-else class="form-card">
      <h2>Login</h2>
      <p v-if="error" class="text-(--color-accent-red) mb-2">{{ error }}</p>
      <form @submit.prevent="handleSubmit">
        <label for="username">Username</label>
        <input id="username" v-model="username" type="text" required />
        <label for="password">Password</label>
        <input id="password" v-model="password" type="password" required />
        <button type="submit">Log In</button>
      </form>
    </div>
  </div>
</template>

<style scoped>
.token-box {
  background: var(--color-bg);
  color: #0f0;
  padding: 1rem;
  border-radius: 6px;
  overflow-x: auto;
  font-size: 0.8rem;
  word-break: break-all;
  white-space: pre-wrap;
}
</style>
