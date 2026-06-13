<template>
  <canvas ref="canvasRef" class="star-field" aria-hidden="true"></canvas>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'

const canvasRef = ref(null)

let animationFrame = 0
let context = null
let dpr = 1
let width = 0
let height = 0
let stars = []
let theme = 'dark'
let reduceMotion = false
let observer = null
let motionQuery = null

const pointer = {
  x: 0,
  y: 0,
  active: false,
  lastSeen: 0,
}

function randomBetween(min, max) {
  return Math.random() * (max - min) + min
}

function getStarCount() {
  return Math.min(190, Math.max(80, Math.round((width * height) / 12000)))
}

function createStar() {
  const size = randomBetween(0.65, 1.85)

  return {
    x: Math.random() * width,
    y: Math.random() * height,
    baseX: 0,
    baseY: 0,
    vx: 0,
    vy: 0,
    size,
    alpha: randomBetween(0.18, 0.72),
    twinkle: randomBetween(0.12, 0.5),
    phase: randomBetween(0, Math.PI * 2),
    colorMix: Math.random(),
  }
}

function syncStarBases() {
  stars.forEach((star) => {
    star.baseX = star.x
    star.baseY = star.y
  })
}

function createStars() {
  stars = Array.from({ length: getStarCount() }, createStar)
  syncStarBases()
}

function updateTheme() {
  theme =
    document.documentElement.getAttribute('data-theme') === 'downtify-light'
      ? 'light'
      : 'dark'
}

function resizeCanvas() {
  const canvas = canvasRef.value
  if (!canvas) return

  dpr = Math.min(window.devicePixelRatio || 1, 2)
  width = window.innerWidth
  height = window.innerHeight

  canvas.width = Math.round(width * dpr)
  canvas.height = Math.round(height * dpr)
  canvas.style.width = `${width}px`
  canvas.style.height = `${height}px`

  context = canvas.getContext('2d')
  context.setTransform(dpr, 0, 0, dpr, 0, 0)
  createStars()
  draw(performance.now())
}

function setPointer(x, y) {
  pointer.x = x
  pointer.y = y
  pointer.active = true
  pointer.lastSeen = performance.now()
}

function handlePointerMove(event) {
  setPointer(event.clientX, event.clientY)
}

function handleTouchMove(event) {
  const touch = event.touches[0]
  if (!touch) return
  setPointer(touch.clientX, touch.clientY)
}

function releasePointer() {
  pointer.active = false
}

function getStarColor(star) {
  if (theme === 'light') {
    return star.colorMix > 0.72 ? '26, 208, 92' : '15, 23, 42'
  }

  return star.colorMix > 0.68 ? '26, 208, 92' : '255, 255, 255'
}

function updateStars(now) {
  const pointerRecentlyActive = now - pointer.lastSeen < 2200
  const pointerStrength = pointer.active || pointerRecentlyActive ? 1 : 0

  stars.forEach((star) => {
    if (!reduceMotion && pointerStrength) {
      const dx = star.x - pointer.x
      const dy = star.y - pointer.y
      const distance = Math.hypot(dx, dy)
      const radius = 150

      if (distance > 0 && distance < radius) {
        const force = (1 - distance / radius) ** 2
        star.vx += (dx / distance) * force * 0.8
        star.vy += (dy / distance) * force * 0.8
      }
    }

    const drift = reduceMotion ? 0 : 0.005
    star.vx += (star.baseX - star.x) * 0.012 + Math.cos(now * 0.0004 + star.phase) * drift
    star.vy += (star.baseY - star.y) * 0.012 + Math.sin(now * 0.00035 + star.phase) * drift
    star.vx *= 0.88
    star.vy *= 0.88
    star.x += star.vx
    star.y += star.vy
  })
}

function draw(now) {
  if (!context) return

  context.clearRect(0, 0, width, height)
  updateStars(now)

  stars.forEach((star) => {
    const twinkle = reduceMotion ? 0 : Math.sin(now * 0.0016 + star.phase) * star.twinkle
    const themeAlpha = theme === 'light' ? 0.55 : 0.82
    const alpha = Math.max(0.05, (star.alpha + twinkle) * themeAlpha)

    context.beginPath()
    context.fillStyle = `rgba(${getStarColor(star)}, ${alpha})`
    context.arc(star.x, star.y, star.size, 0, Math.PI * 2)
    context.fill()
  })

  animationFrame = requestAnimationFrame(draw)
}

function handleMotionPreferenceChange(event) {
  reduceMotion = event.matches
}

onMounted(() => {
  updateTheme()
  motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
  reduceMotion = motionQuery.matches
  motionQuery.addEventListener('change', handleMotionPreferenceChange)

  observer = new MutationObserver(updateTheme)
  observer.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['data-theme'],
  })

  resizeCanvas()
  window.addEventListener('resize', resizeCanvas)
  window.addEventListener('pointermove', handlePointerMove, { passive: true })
  window.addEventListener('pointerleave', releasePointer)
  window.addEventListener('blur', releasePointer)
  window.addEventListener('touchmove', handleTouchMove, { passive: true })
  window.addEventListener('touchend', releasePointer)
})

onBeforeUnmount(() => {
  cancelAnimationFrame(animationFrame)
  observer?.disconnect()
  motionQuery?.removeEventListener('change', handleMotionPreferenceChange)
  window.removeEventListener('resize', resizeCanvas)
  window.removeEventListener('pointermove', handlePointerMove)
  window.removeEventListener('pointerleave', releasePointer)
  window.removeEventListener('blur', releasePointer)
  window.removeEventListener('touchmove', handleTouchMove)
  window.removeEventListener('touchend', releasePointer)
})
</script>
