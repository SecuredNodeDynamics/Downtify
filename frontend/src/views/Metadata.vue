<template>
  <div class="min-h-screen">
    <Navbar />
    <Settings />

    <main class="mx-auto max-w-5xl px-4 py-8 sm:px-6">
      <div class="mb-8 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 class="text-2xl font-bold tracking-tight">
            {{ t('metadata.title') }}
          </h1>
          <p class="mt-1 text-sm text-base-content/60">
            {{ t('metadata.subtitle') }}
          </p>
        </div>
        <div class="flex items-center gap-2">
          <select
            v-model.number="scanLimit"
            class="select h-11 rounded-full border-white/10 bg-base-100/85 text-sm"
            :disabled="loading"
            :title="t('metadata.scanLimit')"
          >
            <option :value="25">25</option>
            <option :value="50">50</option>
            <option :value="100">100</option>
          </select>
          <button
            class="btn btn-primary btn-sm h-11 rounded-full px-5"
            :disabled="loading"
            @click="scan"
          >
            <span
              v-if="loading"
              class="loading loading-spinner loading-xs mr-2"
            />
            <Icon v-else icon="clarity:refresh-line" class="h-4 w-4 mr-2" />
            {{ t('metadata.scan') }}
          </button>
        </div>
      </div>

      <div
        v-if="error"
        class="surface mb-4 flex items-center gap-3 rounded-2xl p-4 text-sm text-error"
      >
        <Icon icon="clarity:exclamation-circle-line" class="h-5 w-5" />
        <span>{{ error }}</span>
      </div>

      <section class="mb-5 grid gap-3 sm:grid-cols-3">
        <div class="surface rounded-2xl p-4">
          <p class="text-xs uppercase text-base-content/40">
            {{ t('metadata.scanned') }}
          </p>
          <p class="mt-1 text-2xl font-semibold">{{ summary.scanned }}</p>
        </div>
        <div class="surface rounded-2xl p-4">
          <p class="text-xs uppercase text-base-content/40">
            {{ t('metadata.needsFix') }}
          </p>
          <p class="mt-1 text-2xl font-semibold text-primary">
            {{ summary.matched }}
          </p>
        </div>
        <div class="surface rounded-2xl p-4">
          <p class="text-xs uppercase text-base-content/40">
            {{ t('metadata.total') }}
          </p>
          <p class="mt-1 text-2xl font-semibold">{{ summary.total }}</p>
        </div>
      </section>

      <p class="mb-5 text-xs text-base-content/45">
        {{ t('metadata.serverOnly') }}
      </p>

      <div v-if="loading && items.length === 0" class="space-y-3">
        <div v-for="n in 5" :key="n" class="skeleton h-24 rounded-2xl" />
      </div>

      <div
        v-else-if="items.length === 0"
        class="surface rounded-2xl p-10 text-center"
      >
        <Icon
          icon="clarity:tag-line"
          class="mx-auto mb-3 h-10 w-10 text-base-content/20"
        />
        <p class="text-sm text-base-content/50">
          {{ t('metadata.empty') }}
        </p>
      </div>

      <ul v-else class="space-y-3">
        <li
          v-for="item in items"
          :key="item.file"
          class="surface rounded-2xl p-4 transition-all duration-300"
          :class="
            applying[item.file]
              ? 'scale-[1.01] border-primary/40 shadow-glow-sm'
              : ''
          "
        >
          <div class="flex flex-wrap items-start justify-between gap-3">
            <div class="min-w-0">
              <p class="truncate text-sm font-semibold">{{ item.file }}</p>
              <p class="mt-1 text-xs text-base-content/45">
                {{ displaySong(item.current) }}
              </p>
            </div>
            <span
              class="pill shrink-0"
              :class="fixed[item.file] ? 'badge-soft' : 'bg-warning/10 text-warning'"
            >
              {{
                fixed[item.file]
                  ? t('metadata.fixed')
                  : t('metadata.needsFix')
              }}
            </span>
          </div>

          <div
            class="mt-4 rounded-xl border border-white/10 bg-base-100/70 p-3"
          >
            <p class="text-xs font-semibold text-primary">
              {{ displaySong(item.candidate) }}
            </p>
            <div
              v-if="item.changes.length"
              class="mt-3 grid gap-2 text-xs sm:grid-cols-2"
            >
              <div
                v-for="change in item.changes"
                :key="`${item.file}-${change.field}`"
                class="rounded-lg bg-white/5 p-2"
              >
                <p class="font-semibold text-base-content/70">
                  {{ change.label }}
                </p>
                <p class="truncate text-base-content/40">
                  {{ change.before || t('metadata.blank') }}
                </p>
                <p class="truncate text-primary">
                  {{ change.after || t('metadata.blank') }}
                </p>
              </div>
            </div>
            <p v-else class="mt-2 text-xs text-base-content/45">
              {{ t('metadata.idsOnly') }}
            </p>
          </div>

          <div class="mt-4 flex justify-end">
            <button
              class="btn btn-sm h-10 rounded-full border-white/10 bg-base-100/85 hover:bg-base-100"
              :class="fixed[item.file] ? 'text-primary' : ''"
              :disabled="applying[item.file] || fixed[item.file]"
              @click="apply(item)"
            >
              <span
                v-if="applying[item.file]"
                class="loading loading-spinner loading-xs mr-2"
              />
              <Icon
                v-else
                icon="clarity:check-line"
                class="h-4 w-4 mr-2"
              />
              {{
                applying[item.file]
                  ? t('metadata.fixing')
                  : fixed[item.file]
                    ? t('metadata.fixed')
                    : t('metadata.apply')
              }}
            </button>
          </div>
        </li>
      </ul>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Icon } from '@iconify/vue'

import Navbar from '/src/components/Navbar.vue'
import Settings from '/src/components/Settings.vue'
import API from '/src/model/api'
import { useI18n } from '/src/i18n'

const { t } = useI18n()
const loading = ref(false)
const error = ref('')
const items = ref([])
const applying = ref({})
const fixed = ref({})
const scanLimit = ref(25)
const summary = ref({ scanned: 0, matched: 0, total: 0 })

function displaySong(song) {
  const artists = (song?.artists || []).join(', ')
  const title = song?.name || t('common.unknownTrack')
  const album = song?.album_name ? ` - ${song.album_name}` : ''
  return `${artists || t('common.unknownArtist')} - ${title}${album}`
}

async function scan() {
  loading.value = true
  error.value = ''
  try {
    const res = await API.scanMetadata(scanLimit.value)
    summary.value = {
      scanned: res.data.scanned || 0,
      matched: res.data.matched || 0,
      total: res.data.total || 0,
    }
    items.value = res.data.items || []
    fixed.value = {}
  } catch {
    error.value = t('metadata.failedScan')
  } finally {
    loading.value = false
  }
}

async function apply(item) {
  applying.value = { ...applying.value, [item.file]: true }
  error.value = ''
  try {
    const res = await API.applyMetadata(item.file)
    fixed.value = { ...fixed.value, [item.file]: true }
    items.value = items.value.map((existing) =>
      existing.file === item.file
        ? { ...existing, current: res.data.current || existing.current }
        : existing
    )
  } catch {
    error.value = t('metadata.failedApply')
  } finally {
    applying.value = { ...applying.value, [item.file]: false }
  }
}
</script>
