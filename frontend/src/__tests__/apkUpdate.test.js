import { describe, expect, it } from 'vitest'
import {
  buildApkUpdateStatus,
  isNewerApkVersion,
  pickApkAsset,
} from '../model/apkUpdate.js'

describe('apkUpdate', () => {
  it('prefers the plain APK name over legacy debug builds', () => {
    const asset = pickApkAsset([
      {
        name: 'downtify-2.10.51-debug.apk',
        browser_download_url: 'https://example.com/debug.apk',
      },
      {
        name: 'downtify-2.10.51.apk',
        browser_download_url: 'https://example.com/release.apk',
      },
    ])

    expect(asset).toMatchObject({
      name: 'downtify-2.10.51.apk',
      version: '2.10.51',
      download_url: 'https://example.com/release.apk',
    })
  })

  it('detects when a GitHub APK is newer than the installed app', () => {
    const status = buildApkUpdateStatus(
      {
        html_url:
          'https://github.com/SecuredNodeDynamics/Downtify/releases/tag/v2.10.52',
        tag_name: 'v2.10.52',
        name: 'Downtify v2.10.52',
        published_at: '2026-06-24T00:00:00Z',
        assets: [
          {
            name: 'downtify-2.10.52.apk',
            browser_download_url: 'https://example.com/downtify-2.10.52.apk',
          },
        ],
      },
      '2.10.51'
    )

    expect(status.update_available).toBe(true)
    expect(status.latest_version).toBe('2.10.52')
    expect(status.apk_download_url).toBe(
      'https://example.com/downtify-2.10.52.apk'
    )
  })

  it('reports up to date when the release APK matches the installed version', () => {
    const status = buildApkUpdateStatus(
      {
        html_url:
          'https://github.com/SecuredNodeDynamics/Downtify/releases/tag/v2.10.51',
        assets: [
          {
            name: 'downtify-2.10.51.apk',
            browser_download_url: 'https://example.com/downtify-2.10.51.apk',
          },
        ],
      },
      '2.10.51'
    )

    expect(status.update_available).toBe(false)
    expect(isNewerApkVersion('2.10.51', '2.10.51')).toBe(false)
  })
})
