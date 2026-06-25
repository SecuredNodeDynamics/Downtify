import { ref } from 'vue'

import API from '/src/model/api'
import { needsServerConnection } from '/src/model/serverConnection'

const settings = ref({
  audio_providers: [''],
  lyrics_providers: [''],
  download_lyrics: true,
  format: '',
  bitrate: '320',
  output: '',
  generate_m3u: true,
  enhance_metadata: true,
  organize_by_artist: false,
  organize_by_album: false,
  server_media_location: '',
  jellyfin_url: '',
  jellyfin_api_key: '',
  jellyfin_music_library: '',
  enable_jellyfin_tools: true,
  artist_folder_policy: 'artwork_available',
  max_parallel_downloads: 3,
})

const settingsOptions = {
  audio_providers: ['youtube', 'youtube-music'],
  lyrics_providers: ['lrclib', 'genius', 'musixmatch', 'azlyrics'],
  format: ['mp3', 'flac', 'ogg', 'opus', 'm4a'],
  bitrate: ['128', '192', '256', '320'],
  artist_folder_policy: ['artwork_available', 'primary_only', 'existing_only'],
  max_parallel_downloads: [1, 2, 3, 5, 8, 12],
  output: '{artists} - {title}.{output-ext}',
}

function isSettingsPayload(data) {
  return Boolean(data) && typeof data === 'object' && !Array.isArray(data)
}

export function loadSettings() {
  if (needsServerConnection()) return Promise.resolve()

  return API.getSettings()
    .then((res) => {
      if (res.status === 200 && isSettingsPayload(res.data)) {
        console.log('Received settings:', res.data)
        settings.value = res.data
      } else {
        console.warn('Ignoring invalid /api/settings response')
      }
    })
    .catch((error) => {
      console.warn('Failed to load settings:', error)
    })
}

loadSettings()

export function getServerMediaLocation() {
  return String(settings.value.server_media_location || '').trim()
}

export function useSettingsManager() {
  const isSaved = ref()
  function saveSettings() {
    if (needsServerConnection()) return

    console.log('Saving settings:', settings.value)
    API.setSettings(settings.value).then((res) => {
      if (res.status === 200) {
        console.log('Saved!')
        isSaved.value = true
        setTimeout(() => {
          isSaved.value = null
        }, 2000)
      } else {
        console.error('Error saving settings.', res)
        isSaved.value = false
        setTimeout(() => {
          isSaved.value = null
        }, 2000)
      }
    })
  }
  return { saveSettings, settings, settingsOptions, isSaved }
}
