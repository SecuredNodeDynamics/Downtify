import { applyPreferredServerRoute } from './model/serverRouteAuto.js'

import '@fontsource/inter/latin-400.css'
import '@fontsource/inter/latin-600.css'
import '@fontsource/inter/latin-700.css'
import './icons/clarity.js'
import './index.css'

async function start() {
  await applyPreferredServerRoute().catch(() => {})
  const [{ createApp }, { default: App }, { default: router }] =
    await Promise.all([
      import('vue'),
      import('./App.vue'),
      import('./router/index'),
    ])
  const app = createApp(App)
  app.use(router)
  app.mount('#app')
}

void start()
