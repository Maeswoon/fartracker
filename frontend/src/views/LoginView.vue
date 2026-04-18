<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const username = ref('')
const password = ref('')
const error = ref<string | null>(null)

async function handleSubmit() {
  error.value = null
  try {
    await auth.login(username.value, password.value)
    const next = route.query.next
    const target = typeof next === 'string' && next.startsWith('/') ? next : '/'
    router.push(target)
  } catch {
    error.value = 'Login failed. Please check your credentials.'
  }
}
</script>

<template>
  <div class="login-wrapper">
    <div class="form-card">
      <h2>Login</h2>
      <p v-if="error" class="error">{{ error }}</p>
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
.login-wrapper {
  display: flex;
  justify-content: center;
  padding: 3rem 1rem;
}

.error {
  color: #dc3545;
  margin-bottom: 0.5rem;
}
</style>
