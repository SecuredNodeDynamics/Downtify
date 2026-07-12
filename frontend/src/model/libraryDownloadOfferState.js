import { reactive } from 'vue'

const offerStates = reactive({})

export function libraryDownloadOfferKey(item, fallback = '') {
  return String(
    item?.browse_id || item?.song_id || item?.url || fallback || ''
  ).trim()
}

export function getLibraryDownloadOfferState(item, fallback = '') {
  const key = libraryDownloadOfferKey(item, fallback)
  return key ? offerStates[key] || '' : ''
}

export function setLibraryDownloadOfferState(item, state, fallback = '') {
  const key = libraryDownloadOfferKey(item, fallback)
  if (!key) return
  if (state) {
    offerStates[key] = state
  } else {
    delete offerStates[key]
  }
}
