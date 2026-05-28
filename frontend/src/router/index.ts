import { createWebHistory, createRouter } from 'vue-router'
import HomeView from '@/views/HomeView.vue'
import TeamView from '@/views/TeamView.vue'
import FrequenciesView from '@/views/FrequenciesView.vue'
import RecoveryView from '@/views/RecoveryView.vue'
import LoginView from '@/views/LoginView.vue'
import AdminView from '@/views/AdminView.vue'
import { getCurrentUser } from '@/api'

const routes = [
  { path: '/', component: HomeView },
  { path: '/frequencies', component: FrequenciesView },
  { path: '/teams/:teamId', component: TeamView },
  { path: '/recovery', component: RecoveryView },
  { path: '/login', component: LoginView },
  { path: '/admin', component: AdminView, meta: { requiresAuth: true } },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  if (to.meta.requiresAuth) {
    try {
      await getCurrentUser()
    } catch {
      return '/login'
    }
  }
})
