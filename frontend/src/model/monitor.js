import axios from 'axios'
import { buildApiBaseUrl, getServerConfig } from './serverConnection.js'

const API = axios.create({
  baseURL: buildApiBaseUrl(getServerConfig()),
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
  return API.patch(`/api/monitor/playlists/${id}`, updates)
}

function deleteMonitoredPlaylist(id) {
  return API.delete(`/api/monitor/playlists/${id}`)
}

function checkMonitoredPlaylist(id) {
  return API.post(`/api/monitor/playlists/${id}/check`)
}

export default {
  listMonitoredPlaylists,
  lookupSpotifyArtists,
  addMonitoredPlaylist,
  updateMonitoredPlaylist,
  deleteMonitoredPlaylist,
  checkMonitoredPlaylist,
}
