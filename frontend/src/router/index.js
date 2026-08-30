import { createWebHistory, createRouter } from 'vue-router'
import config from '/src/config'
import Home from '/src/views/Front.vue'
import { authStatus } from '/src/model/authSession.js'

const Search = () => import('/src/views/Search.vue')
const Download = () => import('/src/views/Download.vue')
const List = () => import('/src/views/Downloads.vue')
const Player = () => import('/src/views/Player.vue')
const Artist = () => import('/src/views/Artist.vue')
const Monitor = () => import('/src/views/Monitor.vue')
const Health = () => import('/src/views/Health.vue')
const Metadata = () => import('/src/views/Metadata.vue')
const Settings = () => import('/src/views/Settings.vue')

const routePreloaders = [Artist, Monitor, Health, Settings]

export function preloadRouteComponents() {
  const preload = () => {
    for (const load of routePreloaders) {
      void load()
    }
  }
  if (typeof window !== 'undefined' && 'requestIdleCallback' in window) {
    window.requestIdleCallback(preload, { timeout: 4000 })
    return
  }
  window.setTimeout(preload, 1200)
}

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home,
    meta: { mobileTitleKey: 'nav.home' },
  },
  {
    path: '/search/:query(.*)',
    name: 'SearchLegacy',
    component: Search,
    meta: { mobileTitleKey: 'nav.search' },
  },
  {
    path: '/search',
    name: 'Search',
    component: Search,
    meta: { mobileTitleKey: 'nav.search' },
  },
  {
    path: '/artist/:browseId?',
    name: 'Artist',
    component: Artist,
    meta: { mobileTitleKey: 'artist.title' },
  },
  {
    path: '/download',
    name: 'Download',
    component: Download,
    meta: { mobileTitleKey: 'nav.queue' },
  },
  {
    path: '/list',
    name: 'List',
    component: List,
    meta: { mobileTitleKey: 'nav.library' },
  },
  {
    path: '/monitor',
    name: 'Monitor',
    component: Monitor,
    meta: { mobileTitleKey: 'nav.monitor' },
  },
  {
    path: '/player',
    name: 'Player',
    component: Player,
    meta: { mobileTitleKey: 'nav.player' },
  },
  {
    path: '/health',
    name: 'Health',
    component: Health,
    meta: { mobileTitleKey: 'nav.health', requiresAdmin: true },
  },
  {
    path: '/metadata',
    name: 'Metadata',
    component: Metadata,
    meta: { mobileTitleKey: 'nav.metadata', requiresAdmin: true },
  },
  {
    path: '/settings',
    name: 'Settings',
    component: Settings,
    meta: { mobileTitleKey: 'nav.settings' },
  },
]

const router = createRouter({
  history: createWebHistory(config.BASEURL),
  routes,
})

router.beforeEach((to) => {
  if (!to.meta?.requiresAdmin) return true
  if (!authStatus.value.auth_required) return true
  if (authStatus.value.user?.is_admin) return true
  return { name: 'Home' }
})

export default router
