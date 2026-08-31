import { createApp } from 'vue'
import App from './App.vue'
import router from './router/index'

import '@fontsource/inter/latin-400.css'
import '@fontsource/inter/latin-600.css'
import '@fontsource/inter/latin-700.css'
import './icons/clarity.js'
import './index.css'

const app = createApp(App)
app.use(router)
app.mount('#app')
