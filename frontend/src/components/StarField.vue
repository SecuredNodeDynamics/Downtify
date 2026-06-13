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
  return Math.min(520, Math.max(180, Math.round((width * height) / 4200)))
}

function createStar() {
  const depth = Math.random()
  const size = randomBetween(0.35, 1.05) + depth * randomBetween(0.25, 1.15)

  return {
    x: Math.random() * width,
    y: Math.random() * height,
    baseX: 0,
    baseY: 0,
    vx: 0,
    vy: 0,
    depth,
    size,
    alpha: randomBetween(0.08, 0.46) + depth * randomBetween(0.12, 0.38),
    twinkle: randomBetween(0.16, 0.62),
    twinkleSpeed: randomBetween(0.00045, 0.00135),
    phase: randomBetween(0, Math.PI * 2),
    colorMix: Math.random(),
    driftAngle: randomBetween(0, Math.PI * 2),
    driftSpeed: randomBetween(0.01, 0.035) + depth * 0.03,
    wander: randomBetween(0.00012, 0.00034),
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

    if (!reduceMotion) {
      star.driftAngle += Math.sin(now * star.wander + star.phase) * 0.0025
    }

    const driftSpeed = reduceMotion ? 0 : star.driftSpeed
    star.vx +=
      (star.baseX - star.x) * 0.006 +
      Math.cos(star.driftAngle) * driftSpeed +
      Math.cos(now * 0.0004 + star.phase) * 0.003
    star.vy +=
      (star.baseY - star.y) * 0.006 +
      Math.sin(star.driftAngle) * driftSpeed +
      Math.sin(now * 0.00035 + star.phase) * 0.003
    star.vx *= 0.88
    star.vy *= 0.88
    star.x += star.vx
    star.y += star.vy

    if (star.x < -12) star.x = width + 12
    if (star.x > width + 12) star.x = -12
    if (star.y < -12) star.y = height + 12
    if (star.y > height + 12) star.y = -12
  })
}

function draw(now) {
  if (!context) return

  context.clearRect(0, 0, width, height)
  updateStars(now)

  stars.forEach((star) => {
    const fade =
      reduceMotion
        ? 0
        : (Math.sin(now * star.twinkleSpeed + star.phase) + 1) * 0.5
    const twinkle = fade * star.twinkle
    const themeAlpha = theme === 'light' ? 0.48 : 0.9
    const alpha = Math.max(0.05, (star.alpha + twinkle) * themeAlpha)
    const glowAlpha = alpha * (theme === 'light' ? 0.18 : 0.28) * star.depth

    if (star.depth > 0.58) {
      context.beginPath()
      context.fillStyle = `rgba(${getStarColor(star)}, ${glowAlpha})`
      context.arc(star.x, star.y, star.size * 2.8, 0, Math.PI * 2)
      context.fill()
    }
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
