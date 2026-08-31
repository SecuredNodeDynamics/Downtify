import { describe, expect, it } from 'vitest'

import {
  canSwitchLoginMethod,
  loginRequestBody,
  preferredLoginMethod,
} from '../model/authLogin.js'

describe('authLogin', () => {
  it('defaults to PIN when the profile has a PIN', () => {
    expect(
      preferredLoginMethod({ has_pin: true, has_password: true })
    ).toBe('pin')
    expect(preferredLoginMethod({ has_pin: true, has_password: false })).toBe(
      'pin'
    )
  })

  it('uses password only when the profile has no PIN', () => {
    expect(
      preferredLoginMethod({ has_pin: false, has_password: true })
    ).toBe('password')
  })

  it('defaults to PIN when the profile is unknown', () => {
    expect(preferredLoginMethod(null)).toBe('pin')
    expect(preferredLoginMethod(undefined)).toBe('pin')
  })

  it('allows switching only when both credentials exist', () => {
    expect(
      canSwitchLoginMethod({ has_pin: true, has_password: true })
    ).toBe(true)
    expect(
      canSwitchLoginMethod({ has_pin: true, has_password: false })
    ).toBe(false)
    expect(canSwitchLoginMethod(null)).toBe(true)
  })

  it('sends only the chosen login secret', () => {
    expect(
      loginRequestBody({
        username: 'admin',
        password: 'secret123',
        pin: '24680',
        method: 'pin',
      })
    ).toEqual({ username: 'admin', password: '', pin: '24680' })
    expect(
      loginRequestBody({
        username: 'admin',
        password: 'secret123',
        pin: '24680',
        method: 'password',
      })
    ).toEqual({ username: 'admin', password: 'secret123', pin: '' })
  })

  it('includes profile_key on login so devices can share a user', () => {
    expect(
      loginRequestBody({
        username: 'Artyom',
        pin: '24680',
        method: 'pin',
        profileKey: '11111111-1111-4111-8111-111111111111',
      })
    ).toEqual({
      username: 'Artyom',
      password: '',
      pin: '24680',
      profile_key: '11111111-1111-4111-8111-111111111111',
    })
  })
})
