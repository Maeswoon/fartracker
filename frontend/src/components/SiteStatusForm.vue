<script setup lang="ts">
import { ref } from 'vue'
import { postSiteStatus } from '@/api'
import { useForm } from '@/api/useApi'

const { success, error, submit } = useForm()

const selected = ref('')
const options = ['Green Flag', 'Yellow Flag', 'Red Flag']

function handleSubmit() {
  submit(() => postSiteStatus(selected.value), 'Failed to post status.')
  selected.value = ''
}
</script>

<template>
  <div class="form-card">
    <h3>Set Site Status</h3>
    <p v-if="success" class="success">Status posted!</p>
    <p v-if="error" class="error">{{ error }}</p>
    <form @submit.prevent="handleSubmit">
      <label>Status</label>
      <select v-model="selected" required>
        <option value="">Select status:</option>
        <option v-for="s in options" :key="s" :value="s">{{ s }}</option>
      </select>
      <button type="submit">Post</button>
    </form>
  </div>
</template>
