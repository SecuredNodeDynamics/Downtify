import { createApp } from 'vue'
import App from './App.vue'
import router from './router/index'
import {
  bootstrapEmbeddedServer,
  EMBEDDED_SERVER_READY_EVENT,
} from './model/embeddedServer'
import { usesEmbeddedServer } from './model/serverConnection'

import './index.css'

async function boot() {
  // Start the on-device backend before mounting so library cover requests do
  // not race a still-booting embedded server on the serverless APK.
  await bootstrapEmbeddedServer()

  const app = createApp(App)
  app.use(router)
  app.mount('#app')

  // Cover components mount after bootstrap may have already emitted ready; fire
  // again so any early failed cover loads retry once the UI is live.
  if (usesEmbeddedServer()) {
    window.dispatchEvent(new CustomEvent(EMBEDDED_SERVER_READY_EVENT))
  }
}

void boot()
