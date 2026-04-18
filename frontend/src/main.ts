import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { router } from '@/router'
import App from '@/App.vue'
import { loadConfig } from '@/config'
import '@/style.css'

loadConfig()
  .catch(err => console.error('Config load failed:', err))
  .finally(() => createApp(App).use(createPinia()).use(router).mount('#app'))
