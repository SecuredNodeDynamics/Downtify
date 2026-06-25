import { ref } from 'vue'

import API from './api'
import { needsServerConnection } from './serverConnection'

// All formats Downtify can be configured to use. The backend reports which of
// these the current host can actually produce (e.g. MP3 needs ffmpeg with
// libmp3lame; FLAC needs ffmpeg's native encoder).
const ALL_AUDIO_FORMATS = ['mp3', 'flac', 'ogg', 'opus', 'm4a']

export const supportedAudioFormats = ref([...ALL_AUDIO_FORMATS])
export const ffmpegAvailable = ref(true)

let loaded = false

export async function loadCapabilities(force = false) {
  if (loaded && !force) return
  if (needsServerConnection()) return

  try {
    const res = await API.getCapabilities()
    const formats = res.data?.audio_formats
    if (Array.isArray(formats) && formats.length) {
      supportedAudioFormats.value = formats.filter((fmt) =>
        ALL_AUDIO_FORMATS.includes(fmt)
      )
    }
    ffmpegAvailable.value = Boolean(res.data?.ffmpeg)
    loaded = true
  } catch {
    // Capabilities are best-effort; keep the optimistic defaults so the user
    // is never blocked from selecting a format.
  }
}
