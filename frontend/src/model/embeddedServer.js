import { registerPlugin } from '@capacitor/core'
import { computed, reactive } from 'vue'

import {
  EMBEDDED_SERVER_URL,
  isEmbeddedServerAvailable,
  usesEmbeddedServer,
} from './serverConnection.js'

const EmbeddedServer = registerPlugin('EmbeddedServer')

export const EMBEDDED_SERVER_READY_EVENT = 'downtify-embedded-server-ready'

const START_PLUGIN_TIMEOUT_MS = 8000
const VERSION_FETCH_TIMEOUT_MS = 2500

const embeddedServerState = reactive({
  starting: false,
  ready: false,
  failed: false,
  error: '',
  baseUrl: EMBEDDED_SERVER_URL,
})

let bootstrapPromise = null

function notifyEmbeddedServerReady() {
  if (typeof window === 'undefined') return
  window.dispatchEvent(new CustomEvent(EMBEDDED_SERVER_READY_EVENT))
}

function withTimeout(promise, ms, label) {
  let timer = 0
  const timeout = new Promise((_, reject) => {
    timer = window.setTimeout(
      () => reject(new Error(`${label} timed out after ${ms}ms`)),
      ms
    )
  })
  return Promise.race([promise, timeout]).finally(() => {
    if (timer) window.clearTimeout(timer)
  })
}

export async function fetchEmbeddedVersion(
  baseUrl,
  timeoutMs = VERSION_FETCH_TIMEOUT_MS
) {
  const url = `${String(baseUrl || '').replace(/\/+$/, '')}/api/version`
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)
  try {
    const res = await fetch(url, {
      cache: 'no-store',
      signal: controller.signal,
    })
    return Boolean(res.ok)
  } catch {
    return false
  } finally {
    clearTimeout(timer)
  }
}

export async function startEmbeddedServer() {
  if (!isEmbeddedServerAvailable()) return null
  try {
    const info = await withTimeout(
      EmbeddedServer.start(),
      START_PLUGIN_TIMEOUT_MS,
      'EmbeddedServer.start'
    )
    return info?.baseUrl || EMBEDDED_SERVER_URL
  } catch (err) {
    console.warn('Could not start embedded server:', err)
    return EMBEDDED_SERVER_URL
  }
}

export function useEmbeddedServerStatus() {
  return {
    starting: computed(() => embeddedServerState.starting),
    ready: computed(() => embeddedServerState.ready),
    failed: computed(() => embeddedServerState.failed),
    error: computed(() => embeddedServerState.error),
    baseUrl: computed(() => embeddedServerState.baseUrl),
  }
}

export async function waitForEmbeddedServer(
  baseUrl,
  {
    attempts = 90,
    delayMs = 1000,
    fetchTimeoutMs = VERSION_FETCH_TIMEOUT_MS,
  } = {}
) {
  for (let i = 0; i < attempts; i += 1) {
    if (await fetchEmbeddedVersion(baseUrl, fetchTimeoutMs)) return true
    if (i < attempts - 1) {
      await new Promise((resolve) => setTimeout(resolve, delayMs))
    }
  }
  return false
}

/**
 * Boot the on-device backend (if this is the embedded APK) and wait until
 * ``/api/version`` answers. Do not reload the WebView afterwards — Capacitor
 * WebViews often drop sessionStorage across ``location.reload()``, which used
 * to restart this loop forever on the splash overlay.
 */
export async function bootstrapEmbeddedServer() {
  if (!isEmbeddedServerAvailable()) return
  if (!usesEmbeddedServer()) return
  if (bootstrapPromise) return bootstrapPromise

  bootstrapPromise = runEmbeddedServerBootstrap().finally(() => {
    bootstrapPromise = null
  })
  return bootstrapPromise
}

export function retryEmbeddedServerBootstrap() {
  bootstrapPromise = null
  embeddedServerState.failed = false
  embeddedServerState.error = ''
  embeddedServerState.ready = false
  return bootstrapEmbeddedServer()
}

async function runEmbeddedServerBootstrap() {
  embeddedServerState.starting = true
  embeddedServerState.failed = false
  embeddedServerState.error = ''

  const baseUrl = (await startEmbeddedServer()) || EMBEDDED_SERVER_URL
  embeddedServerState.baseUrl = baseUrl
  const ready = await waitForEmbeddedServer(baseUrl)
  if (!ready) {
    console.warn('Embedded server did not become ready in time.')
    embeddedServerState.failed = true
    embeddedServerState.error = 'timeout'
    embeddedServerState.starting = false
    return
  }

  embeddedServerState.ready = true
  embeddedServerState.starting = false
  embeddedServerState.failed = false
  embeddedServerState.error = ''
  notifyEmbeddedServerReady()
}
