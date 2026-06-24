import { isCapacitorNative } from './serverConnection.js'

export function usesServerUpdateFlow() {
  return !isCapacitorNative()
}

export function usesApkUpdateFlow() {
  return isCapacitorNative()
}
