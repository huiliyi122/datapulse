import { createRouter, createWebHashHistory } from 'vue-router'

import Dashboard from '@/views/Dashboard.vue'
import Scraper from '@/views/Scraper.vue'
import AIExtract from '@/views/AIExtract.vue'
import TextAnalysis from '@/views/TextAnalysis.vue'
import Login from '@/views/Login.vue'
import Register from '@/views/Register.vue'

const routes = [
  { path: '/', name: 'Dashboard', component: Dashboard, meta: { title: 'Data Dashboard' } },
  { path: '/scraper', name: 'Scraper', component: Scraper, meta: { title: 'Scraper Tasks' } },
  { path: '/ai', name: 'AIExtract', component: AIExtract, meta: { title: 'AI Extract' } },
  { path: '/text', name: 'TextAnalysis', component: TextAnalysis, meta: { title: 'Text Analysis' } },
  { path: '/login', name: 'Login', component: Login, meta: { title: 'Login', guest: true } },
  { path: '/register', name: 'Register', component: Register, meta: { title: 'Register', guest: true } },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

const AUTH_KEY = 'datapulse_token'
const USER_KEY = 'datapulse_user'

export function getToken() {
  return localStorage.getItem(AUTH_KEY)
}

export function setAuth(token, username) {
  localStorage.setItem(AUTH_KEY, token)
  localStorage.setItem(USER_KEY, username)
}

export function clearAuth() {
  localStorage.removeItem(AUTH_KEY)
  localStorage.removeItem(USER_KEY)
}

export function getUsername() {
  return localStorage.getItem(USER_KEY) || ''
}

router.beforeEach((to, from, next) => {
  const token = getToken()
  if (!token && !to.meta.guest) {
    next('/login')
  } else if (token && to.meta.guest) {
    next('/')
  } else {
    next()
  }
})

export default router
