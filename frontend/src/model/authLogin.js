export function preferredLoginMethod(profile) {
  if (profile?.has_pin) return 'pin'
  if (profile?.has_password) return 'password'
  return 'pin'
}

export function canSwitchLoginMethod(profile) {
  if (!profile) return true
  return Boolean(profile.has_pin) && Boolean(profile.has_password)
}

export function loginRequestBody({
  username,
  displayName = '',
  password = '',
  pin = '',
  method = 'pin',
  setup = false,
  profileKey = '',
}) {
  if (setup) {
    return {
      username,
      display_name: displayName,
      password,
      pin,
      profile_key: profileKey,
    }
  }
  if (method === 'password') {
    return { username, password, pin: '' }
  }
  return { username, password: '', pin }
}
