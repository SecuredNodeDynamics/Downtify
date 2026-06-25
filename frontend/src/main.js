import { createApp } from 'vue'
import App from './App.vue'
import router from './router/index'
import { bootstrapEmbeddedServer } from './model/embeddedServer'

import './index.css'

const app = createApp(App)
app.use(router)
app.mount('#app')

// On the serverless APK build this starts the on-device backend and reloads
// once it's reachable. No-op on web and remote-server setups.
void bootstrapEmbeddedServer()
