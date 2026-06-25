import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('../model/api', () => ({
  default: {
    getCapabilities: vi.fn(),
  },
}))

vi.mock('../model/serverConnection', () => ({
  needsServerConnection: vi.fn(() => false),
}))

import API from '../model/api'
import { needsServerConnection } from '../model/serverConnection'

async function freshModule() {
  vi.resetModules()
  return await import('../model/capabilities')
}

describe('capabilities', () => {
  beforeEach(() => {
    API.getCapabilities.mockReset()
    needsServerConnection.mockReturnValue(false)
  })

  it('defaults to the full format list before loading', async () => {
    const mod = await freshModule()
    expect(mod.supportedAudioFormats.value).toEqual([
      'mp3',
      'flac',
      'ogg',
      'opus',
      'm4a',
    ])
  })

  it('narrows formats to what the backend reports', async () => {
    API.getCapabilities.mockResolvedValue({
      data: { ffmpeg: false, audio_formats: ['m4a'] },
    })
    const mod = await freshModule()

    await mod.loadCapabilities()

    expect(mod.supportedAudioFormats.value).toEqual(['m4a'])
    expect(mod.ffmpegAvailable.value).toBe(false)
  })

  it('keeps mp3 and flac when ffmpeg supports them', async () => {
    API.getCapabilities.mockResolvedValue({
      data: { ffmpeg: true, audio_formats: ['mp3', 'flac', 'm4a'] },
    })
    const mod = await freshModule()

    await mod.loadCapabilities()

    expect(mod.supportedAudioFormats.value).toEqual(['mp3', 'flac', 'm4a'])
    expect(mod.ffmpegAvailable.value).toBe(true)
  })

  it('skips probing when a remote server connection is required', async () => {
    needsServerConnection.mockReturnValue(true)
    const mod = await freshModule()

    await mod.loadCapabilities()

    expect(API.getCapabilities).not.toHaveBeenCalled()
  })

  it('keeps optimistic defaults when the request fails', async () => {
    API.getCapabilities.mockRejectedValue(new Error('offline'))
    const mod = await freshModule()

    await mod.loadCapabilities()

    expect(mod.supportedAudioFormats.value).toEqual([
      'mp3',
      'flac',
      'ogg',
      'opus',
      'm4a',
    ])
  })
})
