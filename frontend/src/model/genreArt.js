const GENRE_ART = {
  Pop: {
    gradient: 'linear-gradient(135deg, #f953c6 0%, #b91d73 55%, #7b2ff7 100%)',
    icon: 'mdi:microphone-variant',
  },
  Rock: {
    gradient: 'linear-gradient(135deg, #ff512f 0%, #dd2476 100%)',
    icon: 'mdi:guitar-electric',
  },
  'Hip-Hop': {
    gradient: 'linear-gradient(135deg, #f7971e 0%, #ffd200 100%)',
    icon: 'mdi:headphones',
  },
  'R&B': {
    gradient: 'linear-gradient(135deg, #8e2de2 0%, #4a00e0 100%)',
    icon: 'mdi:heart-pulse',
  },
  Electronic: {
    gradient: 'linear-gradient(135deg, #00c6ff 0%, #0072ff 100%)',
    icon: 'mdi:sine-wave',
  },
  Dance: {
    gradient: 'linear-gradient(135deg, #fc466b 0%, #3f5efb 100%)',
    icon: 'mdi:dance-ballroom',
  },
  Latin: {
    gradient: 'linear-gradient(135deg, #f12711 0%, #f5af19 100%)',
    icon: 'mdi:maracas',
  },
  Jazz: {
    gradient: 'linear-gradient(135deg, #c79081 0%, #dfa579 100%)',
    icon: 'mdi:saxophone',
  },
  Classical: {
    gradient: 'linear-gradient(135deg, #141e30 0%, #243b55 55%, #c9a227 100%)',
    icon: 'mdi:piano',
  },
  Country: {
    gradient: 'linear-gradient(135deg, #56ab2f 0%, #a8e063 100%)',
    icon: 'mdi:hat-cowboy',
  },
  Metal: {
    gradient: 'linear-gradient(135deg, #232526 0%, #414345 100%)',
    icon: 'mdi:skull',
  },
  Indie: {
    gradient: 'linear-gradient(135deg, #834d9b 0%, #d04ed6 100%)',
    icon: 'mdi:flower-tulip',
  },
  Folk: {
    gradient: 'linear-gradient(135deg, #6a9113 0%, #a3c86d 100%)',
    icon: 'mdi:leaf',
  },
  Reggae: {
    gradient: 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)',
    icon: 'mdi:palm-tree',
  },
  Blues: {
    gradient: 'linear-gradient(135deg, #2c3e50 0%, #4ca1af 100%)',
    icon: 'mdi:music-clef-treble',
  },
  Soul: {
    gradient: 'linear-gradient(135deg, #7f00ff 0%, #e100ff 100%)',
    icon: 'mdi:heart',
  },
  Funk: {
    gradient: 'linear-gradient(135deg, #f46b45 0%, #eea849 100%)',
    icon: 'mdi:disc-player',
  },
  Punk: {
    gradient: 'linear-gradient(135deg, #ff0844 0%, #ffb199 100%)',
    icon: 'mdi:lightning-bolt',
  },
  Soundtrack: {
    gradient: 'linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%)',
    icon: 'mdi:movie-open',
  },
  World: {
    gradient: 'linear-gradient(135deg, #1d976c 0%, #93f9b9 100%)',
    icon: 'mdi:earth',
  },
}

const DEFAULT_ART = {
  gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  icon: 'clarity:tags-line',
}

export function genreArtFor(name) {
  const key = String(name || '').trim()
  return GENRE_ART[key] || DEFAULT_ART
}

export function genreCoverStyle(name) {
  const art = genreArtFor(name)
  return {
    background: art.gradient,
  }
}

export function genreCoverIcon(name) {
  return genreArtFor(name).icon
}

export function genreOverlayStyle(name) {
  const art = genreArtFor(name)
  return {
    background: art.gradient,
    opacity: '0.42',
  }
}
