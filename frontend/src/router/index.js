import { createWebHistory, createRouter } from 'vue-router'
import config from '/src/config'

const Home = () => import('/src/views/Front.vue')
const Search = () => import('/src/views/Search.vue')
const Download = () => import('/src/views/Download.vue')
const List = () => import('/src/views/Downloads.vue')
const Monitor = () => import('/src/views/Monitor.vue')
const Player = () => import('/src/views/Player.vue')
const Health = () => import('/src/views/Health.vue')
const Metadata = () => import('/src/views/Metadata.vue')
const Settings = () => import('/src/views/Settings.vue')

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
    meta: { mobileTitleKey: 'nav.health' },
  },
  {
    path: '/metadata',
    name: 'Metadata',
    component: Metadata,
    meta: { mobileTitleKey: 'nav.metadata' },
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

export default router
