import { isCapacitorNative, usesCustomServerUrl } from './serverConnection.js'

export function usesServerUpdateFlow() {
  return !isCapacitorNative() || usesCustomServerUrl()
}

export function usesApkUpdateFlow() {
  return isCapacitorNative() && !usesCustomServerUrl()
}
