import axios from 'axios'
import { buildApiBaseUrl, getServerConfig } from './serverConnection.js'

const API = axios.create()

API.interceptors.request.use((config) => {
  config.baseURL = buildApiBaseUrl(getServerConfig())
  return config
})

function listMonitoredPlaylists() {
  return API.get('/api/monitor/playlists')
}

function lookupSpotifyArtists(artistName, limit = 5) {
  return API.get('/api/monitor/artists/lookup', {
    params: { artist: artistName, limit },
    timeout: 30000,
  })
}

function addMonitoredPlaylist(url, intervalMinutes = 60, kind = 'playlist') {
  return API.post('/api/monitor/playlists', {
    url,
    interval_minutes: intervalMinutes,
    kind,
  })
}

function updateMonitoredPlaylist(id, updates) {
  return API.post(`/api/monitor/playlists/${id}/update`, updates, {
    timeout: 15000,
    headers: { 'Content-Type': 'application/json' },
  })
}

function deleteMonitoredPlaylist(id) {
  return API.delete(`/api/monitor/playlists/${id}`)
}

function checkMonitoredPlaylist(id) {
  return API.post(`/api/monitor/playlists/${id}/check`, null, {
    timeout: 300000,
    headers: { 'Content-Type': 'application/json' },
  })
}

export default {
  listMonitoredPlaylists,
  lookupSpotifyArtists,
  addMonitoredPlaylist,
  updateMonitoredPlaylist,
  deleteMonitoredPlaylist,
  checkMonitoredPlaylist,
}
