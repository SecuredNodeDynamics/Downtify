/**
 * Playback-recovery policy for streamed audio.
 *
 * When the player streams from a remote Downtify server (the "server
 * connected" Android mode or the web app), a flaky network can momentarily
 * starve the HTML5 audio element. The element then fires ``waiting`` /
 * ``stalled`` or a transient ``error`` and stays paused, so the music
 * "randomly" stops. Local embedded playback reads files off disk and never
 * hits this, so recovery is intentionally limited to streamed sources.
 *
 * These helpers are pure so the back-off and "should we reload?" decision can
 * be unit tested without a DOM media element.
 */

export const MAX_RECOVERY_ATTEMPTS = 8
export const BASE_RECOVERY_DELAY_MS = 600
export const MAX_RECOVERY_DELAY_MS = 8000

// HTMLMediaElement.readyState >= HAVE_FUTURE_DATA (3) means the element has
// enough buffered data to keep playing, so a stall has cleared.
export const HEALTHY_READY_STATE = 3

/** Exponential back-off (capped) between successive recovery attempts. */
export function recoveryDelayMs(
  attempt,
  { base = BASE_RECOVERY_DELAY_MS, max = MAX_RECOVERY_DELAY_MS } = {}
) {
  const n = Math.max(0, Math.floor(Number(attempt) || 0))
  return Math.min(max, base * 2 ** n)
}

/**
 * Decide whether a stalled/errored stream warrants a reload-and-resume.
 *
 * Returns ``false`` when playback wasn't wanted, the source is a local file,
 * the user is actively seeking, we've exhausted attempts, or the element is
 * already healthy (playing with enough buffered data).
 */
export function shouldRecoverPlayback({
  playbackIntent,
  streamed,
  paused,
  seeking = false,
  readyState = 0,
  attempts = 0,
  maxAttempts = MAX_RECOVERY_ATTEMPTS,
} = {}) {
  if (!playbackIntent) return false
  if (!streamed) return false
  if (seeking) return false
  if (attempts >= maxAttempts) return false
  if (!paused && Number(readyState) >= HEALTHY_READY_STATE) return false
  return true
}
