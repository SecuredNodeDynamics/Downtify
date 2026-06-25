const DB_NAME = 'downtify-image-cache'
const STORE_NAME = 'images'
const DB_VERSION = 1
const MAX_ENTRIES = 500

let dbPromise = null

function openDb() {
  if (dbPromise) return dbPromise
  if (typeof indexedDB === 'undefined') {
    dbPromise = Promise.resolve(null)
    return dbPromise
  }

  dbPromise = new Promise((resolve) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION)
    request.onupgradeneeded = () => {
      const db = request.result
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        const store = db.createObjectStore(STORE_NAME, { keyPath: 'key' })
        store.createIndex('updatedAt', 'updatedAt', { unique: false })
      }
    }
    request.onsuccess = () => resolve(request.result)
    request.onerror = () => resolve(null)
  })

  return dbPromise
}

function cacheKey(url) {
  return String(url || '').trim()
}

export async function readPersistedImage(url) {
  const key = cacheKey(url)
  if (!key) return null

  const db = await openDb()
  if (!db) return null

  return new Promise((resolve) => {
    const tx = db.transaction(STORE_NAME, 'readonly')
    const request = tx.objectStore(STORE_NAME).get(key)
    request.onsuccess = () => {
      const record = request.result
      resolve(record?.blob instanceof Blob ? record.blob : null)
    }
    request.onerror = () => resolve(null)
  })
}

async function trimCache(db) {
  const count = await new Promise((resolve) => {
    const request = db.transaction(STORE_NAME, 'readonly').objectStore(STORE_NAME).count()
    request.onsuccess = () => resolve(request.result || 0)
    request.onerror = () => resolve(0)
  })

  if (count <= MAX_ENTRIES) return

  const toDelete = count - MAX_ENTRIES
  let deleted = 0

  await new Promise((resolve) => {
    const tx = db.transaction(STORE_NAME, 'readwrite')
    const index = tx.objectStore(STORE_NAME).index('updatedAt')
    const cursorRequest = index.openCursor()
    cursorRequest.onsuccess = () => {
      const cursor = cursorRequest.result
      if (!cursor || deleted >= toDelete) {
        resolve()
        return
      }
      cursor.delete()
      deleted += 1
      cursor.continue()
    }
    cursorRequest.onerror = () => resolve()
  })
}

export async function writePersistedImage(url, blob) {
  const key = cacheKey(url)
  if (!key || !(blob instanceof Blob)) return

  const db = await openDb()
  if (!db) return

  await new Promise((resolve) => {
    const tx = db.transaction(STORE_NAME, 'readwrite')
    tx.oncomplete = () => resolve()
    tx.onerror = () => resolve()
    tx.objectStore(STORE_NAME).put({
      key,
      blob,
      updatedAt: Date.now(),
    })
  })

  void trimCache(db)
}

export async function clearPersistedImageCache() {
  const db = await openDb()
  if (!db) return

  await new Promise((resolve) => {
    const tx = db.transaction(STORE_NAME, 'readwrite')
    tx.oncomplete = () => resolve()
    tx.onerror = () => resolve()
    tx.objectStore(STORE_NAME).clear()
  })
}
