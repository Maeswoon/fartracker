import { createWebHistory, createRouter } from 'vue-router'
import { getCurrentUser } from '@/api'

const routes = [
  { path: '/', component: () => import('@/views/HomeView.vue') },
  { path: '/frequencies', component: () => import('@/views/FrequenciesView.vue'), meta: { requiresAdmin: true } },
  { path: '/teams/:teamId', component: () => import('@/views/TeamView.vue') },
  { path: '/recovery', component: () => import('@/views/RecoveryView.vue') },
  { path: '/schedule', component: () => import('@/views/ScheduleView.vue') },
  { path: '/login', component: () => import('@/views/LoginView.vue') },
  { path: '/admin', component: () => import('@/views/AdminView.vue'), meta: { requiresAdmin: true } },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  if (to.meta.requiresAdmin) {
    try {
      const user = await getCurrentUser()
      if (!user.is_admin) return '/'
    } catch {
      return '/login'
    }
  }
})
