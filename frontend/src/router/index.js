import { createRouter, createWebHashHistory } from 'vue-router'

import Dashboard from '@/views/Dashboard.vue'
import Scraper from '@/views/Scraper.vue'
import AIExtract from '@/views/AIExtract.vue'
import TextAnalysis from '@/views/TextAnalysis.vue'

const routes = [
  { path: '/', name: 'Dashboard', component: Dashboard, meta: { title: 'Data Dashboard' } },
  { path: '/scraper', name: 'Scraper', component: Scraper, meta: { title: 'Scraper Tasks' } },
  { path: '/ai', name: 'AIExtract', component: AIExtract, meta: { title: 'AI Extract' } },
  { path: '/text', name: 'TextAnalysis', component: TextAnalysis, meta: { title: 'Text Analysis' } },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

export default router
