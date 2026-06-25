import { registerPlugin } from '@capacitor/core'

import {
  EMBEDDED_SERVER_URL,
  isEmbeddedServerAvailable,
  usesEmbeddedServer,
} from './serverConnection.js'

const EmbeddedServer = registerPlugin('EmbeddedServer')

const READY_FLAG = 'downtify-embedded-ready'
export const EMBEDDED_SERVER_READY_EVENT = 'downtify-embedded-server-ready'

function notifyEmbeddedServerReady() {
  if (typeof window === 'undefined') return
  window.dispatchEvent(new CustomEvent(EMBEDDED_SERVER_READY_EVENT))
}

export async function startEmbeddedServer() {
  if (!isEmbeddedServerAvailable()) return null
  try {
    const info = await EmbeddedServer.start()
    return info?.baseUrl || EMBEDDED_SERVER_URL
  } catch (err) {
    console.warn('Could not start embedded server:', err)
    return null
  }
}

export async function waitForEmbeddedServer(
  baseUrl,
  { attempts = 90, delayMs = 1000 } = {}
) {
  for (let i = 0; i < attempts; i += 1) {
    try {
      const res = await fetch(`${baseUrl}/api/version`, { cache: 'no-store' })
      if (res.ok) return true
    } catch {
      // Server not up yet; keep polling.
    }
    await new Promise((resolve) => setTimeout(resolve, delayMs))
  }
  return false
}

/**
 * Boot the on-device backend (if this is the embedded APK) and reload once it
 * is reachable so the app re-initialises against the now-live local server.
 * No-op on web and when the user has configured a remote server.
 */
export async function bootstrapEmbeddedServer() {
  if (!isEmbeddedServerAvailable()) return
  // Only boot the local backend when the user is in on-device mode.
  if (!usesEmbeddedServer()) return

  const baseUrl = (await startEmbeddedServer()) || EMBEDDED_SERVER_URL
  const ready = await waitForEmbeddedServer(baseUrl)
  if (!ready) {
    console.warn('Embedded server did not become ready in time.')
    return
  }

  notifyEmbeddedServerReady()

  let alreadyReady = false
  try {
    alreadyReady = sessionStorage.getItem(READY_FLAG) === '1'
    sessionStorage.setItem(READY_FLAG, '1')
  } catch {
    // sessionStorage unavailable; fall through and reload once.
  }

  if (!alreadyReady) {
    window.location.reload()
  }
}
