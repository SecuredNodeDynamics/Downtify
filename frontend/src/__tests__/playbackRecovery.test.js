import { describe, expect, it } from 'vitest'

import {
  MAX_RECOVERY_ATTEMPTS,
  recoveryDelayMs,
  shouldRecoverPlayback,
} from '../model/playbackRecovery.js'

const streamingStall = {
  playbackIntent: true,
  streamed: true,
  paused: true,
  seeking: false,
  readyState: 1,
  attempts: 0,
}

describe('recoveryDelayMs', () => {
  it('backs off exponentially and caps', () => {
    expect(recoveryDelayMs(0)).toBe(600)
    expect(recoveryDelayMs(1)).toBe(1200)
    expect(recoveryDelayMs(2)).toBe(2400)
    expect(recoveryDelayMs(10)).toBe(8000)
  })

  it('treats invalid attempts as zero', () => {
    expect(recoveryDelayMs(undefined)).toBe(600)
    expect(recoveryDelayMs(-5)).toBe(600)
  })
})

describe('shouldRecoverPlayback', () => {
  it('recovers a streamed source that stalled while playback was wanted', () => {
    expect(shouldRecoverPlayback(streamingStall)).toBe(true)
  })

  it('does nothing when playback was not intended', () => {
    expect(
      shouldRecoverPlayback({ ...streamingStall, playbackIntent: false })
    ).toBe(false)
  })

  it('never reloads local embedded files', () => {
    expect(shouldRecoverPlayback({ ...streamingStall, streamed: false })).toBe(
      false
    )
  })

  it('does not fight an active user seek', () => {
    expect(shouldRecoverPlayback({ ...streamingStall, seeking: true })).toBe(
      false
    )
  })

  it('stops after exhausting the attempt budget', () => {
    expect(
      shouldRecoverPlayback({
        ...streamingStall,
        attempts: MAX_RECOVERY_ATTEMPTS,
      })
    ).toBe(false)
  })

  it('leaves healthy playback alone', () => {
    expect(
      shouldRecoverPlayback({
        ...streamingStall,
        paused: false,
        readyState: 4,
      })
    ).toBe(false)
  })

  it('still recovers when playing but starved of buffered data', () => {
    expect(
      shouldRecoverPlayback({
        ...streamingStall,
        paused: false,
        readyState: 2,
      })
    ).toBe(true)
  })
})
