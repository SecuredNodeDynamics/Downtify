import { ref, computed } from 'vue'

const DESTINATION_KEY = 'downtify-download-destination'
const FOLDER_NAME_KEY = 'downtify-local-folder-name'
const HANDLE_DB = 'downtify-fs'
const HANDLE_STORE = 'directory'

const destination = ref(readDestination())
const localFolderName = ref(readFolderName())

let dirHandle = null

function readDestination() {
  const value = localStorage.getItem(DESTINATION_KEY)
  return value === 'local' ? 'local' : 'server'
}

function readFolderName() {
  return localStorage.getItem(FOLDER_NAME_KEY) || ''
}

function supportsLocalFolder() {
  return typeof window !== 'undefined' && 'showDirectoryPicker' in window
}

function openHandleDb() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(HANDLE_DB, 1)
    request.onupgradeneeded = () => {
      request.result.createObjectStore(HANDLE_STORE)
    }
    request.onsuccess = () => resolve(request.result)
    request.onerror = () => reject(request.error)
  })
}

async function loadStoredHandle() {
  if (!supportsLocalFolder()) return null
  try {
    const db = await openHandleDb()
    const handle = await new Promise((resolve, reject) => {
      const tx = db.transaction(HANDLE_STORE, 'readonly')
      const req = tx.objectStore(HANDLE_STORE).get('downloads')
      req.onsuccess = () => resolve(req.result || null)
      req.onerror = () => reject(req.error)
    })
    if (!handle) return null

    const permission = await handle.queryPermission({ mode: 'readwrite' })
    if (permission === 'granted') {
      dirHandle = handle
      return handle
    }
    const requested = await handle.requestPermission({ mode: 'readwrite' })
    if (requested === 'granted') {
      dirHandle = handle
      return handle
    }
  } catch (err) {
    console.warn('Could not restore local download folder:', err)
  }
  return null
}

async function persistHandle(handle) {
  const db = await openHandleDb()
  await new Promise((resolve, reject) => {
    const tx = db.transaction(HANDLE_STORE, 'readwrite')
    tx.objectStore(HANDLE_STORE).put(handle, 'downloads')
    tx.oncomplete = () => resolve()
    tx.onerror = () => reject(tx.error)
  })
}

async function clearStoredHandle() {
  try {
    const db = await openHandleDb()
    await new Promise((resolve, reject) => {
      const tx = db.transaction(HANDLE_STORE, 'readwrite')
      tx.objectStore(HANDLE_STORE).delete('downloads')
      tx.oncomplete = () => resolve()
      tx.onerror = () => reject(tx.error)
    })
  } catch {
    // ignore
  }
}

function setDestination(value) {
  destination.value = value === 'local' ? 'local' : 'server'
  try {
    localStorage.setItem(DESTINATION_KEY, destination.value)
  } catch {
    // ignore
  }
}

async function pickLocalFolder() {
  if (!supportsLocalFolder()) return false
  const handle = await window.showDirectoryPicker({ mode: 'readwrite' })
  dirHandle = handle
  localFolderName.value = handle.name
  try {
    localStorage.setItem(FOLDER_NAME_KEY, handle.name)
  } catch {
    // ignore
  }
  await persistHandle(handle)
  return true
}

async function clearLocalFolder() {
  dirHandle = null
  localFolderName.value = ''
  try {
    localStorage.removeItem(FOLDER_NAME_KEY)
  } catch {
    // ignore
  }
  await clearStoredHandle()
}

async function ensureDirHandle(root, parts) {
  let current = root
  for (const part of parts) {
    current = await current.getDirectoryHandle(part, { create: true })
  }
  return current
}

async function writeBlobToFolder(relativePath, blob) {
  const handle = dirHandle || (await loadStoredHandle())
  if (!handle) return false

  const segments = String(relativePath || '')
    .split('/')
    .filter(Boolean)
  if (!segments.length) return false

  const fileName = segments.pop()
  const dir = segments.length
    ? await ensureDirHandle(handle, segments)
    : handle
  const fileHandle = await dir.getFileHandle(fileName, { create: true })
  const writable = await fileHandle.createWritable()
  await writable.write(blob)
  await writable.close()
  return true
}

function triggerBrowserDownload(blob, filename) {
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = String(filename || 'download').split('/').pop() || 'download'
  document.body.appendChild(anchor)
  anchor.click()
  document.body.removeChild(anchor)
  URL.revokeObjectURL(url)
}

async function saveToLocalMachine(downloadUrl, filename) {
  if (destination.value !== 'local' || !downloadUrl) return

  const response = await fetch(downloadUrl)
  if (!response.ok) {
    throw new Error(`Download failed (${response.status})`)
  }
  const blob = await response.blob()

  if (filename) {
    try {
      const savedToFolder = await writeBlobToFolder(filename, blob)
      if (savedToFolder) return
    } catch (err) {
      console.warn('Saving to chosen folder failed, using browser download:', err)
    }
  }

  triggerBrowserDownload(blob, filename)
}

loadStoredHandle()

export function useDownloadDestination() {
  return {
    destination,
    localFolderName,
    supportsLocalFolder: computed(() => supportsLocalFolder()),
    isLocal: computed(() => destination.value === 'local'),
    setDestination,
    pickLocalFolder,
    clearLocalFolder,
    saveToLocalMachine,
  }
}
