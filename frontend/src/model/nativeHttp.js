import { CapacitorHttp } from '@capacitor/core'
import axios, { AxiosError } from 'axios'

import { isCapacitorNative } from './serverConnection.js'

// Large JSON payloads are cheaper to parse in the WebView than to shuttle
// through the Capacitor JS bridge. Keep those on the default axios adapter.
const LARGE_JSON_PATHS = [
  '/api/library/files',
  '/list',
  '/api/metadata/duplicates',
]

export function requestPath(config) {
  const raw = String(config?.url || '')
  const base = String(config?.baseURL || 'http://downtify.local')
  try {
    return new URL(raw, base.endsWith('/') ? base : `${base}/`).pathname
  } catch {
    return raw.split('?')[0] || ''
  }
}

export function shouldUseNativeHttpAdapter(config = {}) {
  if (!isCapacitorNative()) return false
  if (typeof CapacitorHttp?.request !== 'function') return false
  const responseType = String(config.responseType || 'json')
  if (responseType && !['json', 'text', ''].includes(responseType)) {
    return false
  }
  const path = requestPath(config)
  return !LARGE_JSON_PATHS.some(
    (prefix) => path === prefix || path.endsWith(prefix)
  )
}

function serializeHeaders(headers) {
  if (!headers) return {}
  const json =
    typeof headers.toJSON === 'function' ? headers.toJSON() : { ...headers }
  const skip = new Set([
    'common',
    'delete',
    'get',
    'head',
    'post',
    'put',
    'patch',
  ])
  const out = {}
  for (const [key, value] of Object.entries(json)) {
    if (value == null || skip.has(key) || typeof value === 'object') continue
    out[key] = String(value)
  }
  return out
}

export async function capacitorAxiosAdapter(config) {
  const method = String(config.method || 'get').toUpperCase()
  const timeout = Number(config.timeout)
  const options = {
    url: axios.getUri(config),
    method,
    headers: serializeHeaders(config.headers),
    responseType: config.responseType === 'text' ? 'text' : 'json',
  }
  if (method !== 'GET' && method !== 'HEAD' && config.data !== undefined) {
    options.data = config.data
  }
  if (Number.isFinite(timeout) && timeout > 0) {
    options.connectTimeout = timeout
    options.readTimeout = timeout
  }

  try {
    const response = await CapacitorHttp.request(options)
    const axiosResponse = {
      data: response.data,
      status: response.status,
      statusText: String(response.status),
      headers: response.headers || {},
      config,
      request: null,
    }
    const validate =
      config.validateStatus || ((status) => status >= 200 && status < 300)
    if (!validate(response.status)) {
      throw new AxiosError(
        `Request failed with status code ${response.status}`,
        response.status >= 500
          ? AxiosError.ERR_BAD_RESPONSE
          : AxiosError.ERR_BAD_REQUEST,
        config,
        null,
        axiosResponse
      )
    }
    return axiosResponse
  } catch (error) {
    if (error instanceof AxiosError) throw error
    throw new AxiosError(
      error?.message || 'Network Error',
      AxiosError.ERR_NETWORK,
      config,
      null
    )
  }
}
