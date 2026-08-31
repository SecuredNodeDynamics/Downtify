const GENRE_ART = {
  Pop: {
    gradient: 'linear-gradient(135deg, #f953c6 0%, #b91d73 55%, #7b2ff7 100%)',
    icon: 'clarity:music-note-line',
  },
  Rock: {
    gradient: 'linear-gradient(135deg, #ff512f 0%, #dd2476 100%)',
    icon: 'clarity:music-note-line',
  },
  'Hip-Hop': {
    gradient: 'linear-gradient(135deg, #f7971e 0%, #ffd200 100%)',
    icon: 'clarity:headphones-line',
  },
  'R&B': {
    gradient: 'linear-gradient(135deg, #8e2de2 0%, #4a00e0 100%)',
    icon: 'clarity:tag-line',
  },
  Electronic: {
    gradient: 'linear-gradient(135deg, #00c6ff 0%, #0072ff 100%)',
    icon: 'clarity:headphones-line',
  },
  Dance: {
    gradient: 'linear-gradient(135deg, #fc466b 0%, #3f5efb 100%)',
    icon: 'clarity:play-solid',
  },
  Latin: {
    gradient: 'linear-gradient(135deg, #f12711 0%, #f5af19 100%)',
    icon: 'clarity:music-note-line',
  },
  Jazz: {
    gradient: 'linear-gradient(135deg, #c79081 0%, #dfa579 100%)',
    icon: 'clarity:music-note-line',
  },
  Swing: {
    gradient: 'linear-gradient(135deg, #c79081 0%, #dfa579 100%)',
    icon: 'clarity:music-note-line',
  },
  Classical: {
    gradient: 'linear-gradient(135deg, #141e30 0%, #243b55 55%, #c9a227 100%)',
    icon: 'clarity:music-note-line',
  },
  Country: {
    gradient: 'linear-gradient(135deg, #56ab2f 0%, #a8e063 100%)',
    icon: 'clarity:music-note-line',
  },
  Metal: {
    gradient: 'linear-gradient(135deg, #232526 0%, #414345 100%)',
    icon: 'clarity:warning-line',
  },
  Indie: {
    gradient: 'linear-gradient(135deg, #834d9b 0%, #d04ed6 100%)',
    icon: 'clarity:tag-line',
  },
  Folk: {
    gradient: 'linear-gradient(135deg, #6a9113 0%, #a3c86d 100%)',
    icon: 'clarity:music-note-line',
  },
  Reggae: {
    gradient: 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)',
    icon: 'clarity:music-note-line',
  },
  Blues: {
    gradient: 'linear-gradient(135deg, #2c3e50 0%, #4ca1af 100%)',
    icon: 'clarity:music-note-line',
  },
  Soul: {
    gradient: 'linear-gradient(135deg, #7f00ff 0%, #e100ff 100%)',
    icon: 'clarity:tag-line',
  },
  Funk: {
    gradient: 'linear-gradient(135deg, #f46b45 0%, #eea849 100%)',
    icon: 'clarity:cd-dvd-line',
  },
  Punk: {
    gradient: 'linear-gradient(135deg, #ff0844 0%, #ffb199 100%)',
    icon: 'clarity:warning-line',
  },
  Soundtrack: {
    gradient: 'linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%)',
    icon: 'clarity:play-solid',
  },
  World: {
    gradient: 'linear-gradient(135deg, #1d976c 0%, #93f9b9 100%)',
    icon: 'clarity:tags-line',
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
