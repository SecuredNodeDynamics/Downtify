<template>
  <input type="checkbox" id="settings-modal" class="modal-toggle" />
  <div class="modal modal-bottom sm:modal-middle">
    <div
      class="modal-box surface-strong rounded-t-3xl sm:rounded-3xl p-0 max-w-lg"
    >
      <!-- Header -->
      <div
        class="flex items-center justify-between px-6 py-4 border-b border-white/5"
      >
        <div>
          <h3 class="text-lg font-bold tracking-tight">
            {{ t('settings.title') }}
          </h3>
          <p class="text-xs text-base-content/50 mt-0.5">
            {{ t('settings.subtitle') }}
          </p>
        </div>
        <label
          for="settings-modal"
          class="icon-btn cursor-pointer"
          :title="t('common.close')"
        >
          <Icon icon="clarity:close-line" class="h-5 w-5" />
        </label>
      </div>

      <!-- Body -->
      <div class="px-6 py-5 space-y-6">
        <!-- Language -->
        <div>
          <label
            class="block text-xs font-semibold uppercase tracking-wider text-base-content/50 mb-2"
          >
            {{ t('settings.language') }}
          </label>
          <select
            class="select w-full rounded-xl bg-base-100/85 border border-white/10 focus:border-primary/60"
            :value="locale"
            @change="setLocale($event.target.value)"
          >
            <option v-for="l in locales" :key="l.code" :value="l.code">
              {{ l.name }}
            </option>
          </select>
          <p class="text-[11px] text-base-content/40 mt-1.5">
            {{ t('settings.languageHint') }}
          </p>
        </div>

        <!-- Download destination -->
        <div>
          <label
            class="block text-xs font-semibold uppercase tracking-wider text-base-content/50 mb-2"
          >
            {{ t('settings.downloadDestination') }}
          </label>
          <div class="grid grid-cols-2 gap-2">
            <button
              type="button"
              class="rounded-xl border px-3 py-2 text-sm transition-colors text-left"
              :class="[
                destination === 'server'
                  ? 'border-primary/50 bg-primary/10 text-primary'
                  : 'border-white/10 hover:border-white/20 hover:bg-white/5',
              ]"
              @click="setDestination('server')"
            >
              {{ t('settings.downloadDestinationServer') }}
            </button>
            <button
              type="button"
              class="rounded-xl border px-3 py-2 text-sm transition-colors text-left"
              :class="[
                destination === 'local'
                  ? 'border-primary/50 bg-primary/10 text-primary'
                  : 'border-white/10 hover:border-white/20 hover:bg-white/5',
              ]"
              @click="selectLocalDestination"
            >
              {{ t('settings.downloadDestinationLocal') }}
            </button>
          </div>
          <p class="text-[11px] text-base-content/40 mt-1.5">
            {{
              destination === 'local'
                ? localDestinationHint
                : t('settings.downloadDestinationServerHint')
            }}
          </p>
          <p
            v-if="localFolderBlockReason"
            class="text-[11px] text-base-content/40 mt-1.5"
          >
            {{ localFolderBlockMessage }}
          </p>
          <div
            v-if="isLocal"
            class="mt-3 rounded-xl border border-white/10 bg-base-100/85 px-3 py-3 space-y-2"
          >
            <div class="flex items-start gap-3">
              <Icon
                icon="clarity:folder-open-line"
                class="mt-0.5 h-5 w-5 shrink-0 text-primary"
              />
              <div class="min-w-0 flex-1">
                <p class="text-sm font-medium">
                  {{ t('settings.localFolderLabel') }}
                </p>
                <p class="truncate text-sm text-base-content/80">
                  {{ localFolderName }}
                </p>
                <p class="mt-1 text-[11px] text-base-content/40">
                  {{
                    usesBrowserDownloads
                      ? t('settings.browserDownloadsHint')
                      : t('settings.localFolderNameHint')
                  }}
                </p>
              </div>
            </div>
            <div class="flex flex-wrap items-center gap-2">
              <button
                v-if="!usesBrowserDownloads"
                type="button"
                class="btn btn-sm h-9 rounded-full border-white/10 bg-base-100/85 hover:bg-base-100"
                @click="changeLocalFolder"
              >
                {{ t('settings.changeLocalFolder') }}
              </button>
            </div>
            <p
              v-if="!localFolderReady"
              class="text-[11px] text-warning"
            >
              {{ t('settings.localFolderPermissionNeeded') }}
            </p>
          </div>
          <p v-if="folderPickerError" class="text-[11px] text-error mt-2">
            {{ folderPickerError }}
          </p>
        </div>

        <!-- Audio source -->
        <div>
          <label
            class="block text-xs font-semibold uppercase tracking-wider text-base-content/50 mb-2"
          >
            {{ t('settings.audioSource') }}
          </label>
          <div class="grid grid-cols-2 gap-2">
            <button
              v-for="provider in sm.settingsOptions.audio_providers"
              :key="provider"
              type="button"
              class="rounded-xl border px-3 py-2 text-sm transition-colors text-left"
              :class="[
                sm.settings.value.audio_providers[0] === provider
                  ? 'border-primary/50 bg-primary/10 text-primary'
                  : 'border-white/10 hover:border-white/20 hover:bg-white/5',
              ]"
              @click="sm.settings.value.audio_providers = [provider]"
            >
              {{ providerLabel(provider) }}
            </button>
          </div>
        </div>

        <!-- Lyrics source -->
        <div>
          <label
            class="block text-xs font-semibold uppercase tracking-wider text-base-content/50 mb-2"
          >
            {{ t('settings.lyricsSource') }}
          </label>
          <label
            class="flex items-start gap-3 rounded-xl border border-white/10 bg-base-100/85 px-3 py-2.5 cursor-pointer hover:border-white/20 mb-2"
          >
            <input
              type="checkbox"
              class="checkbox checkbox-sm checkbox-primary mt-0.5"
              v-model="sm.settings.value.download_lyrics"
            />
            <span class="flex-1 text-sm">
              <span class="block">{{ t('settings.downloadLyrics') }}</span>
              <span class="block text-[11px] text-base-content/50">
                {{ t('settings.downloadLyricsHint') }}
              </span>
            </span>
          </label>
          <div class="flex items-baseline justify-between mb-1.5">
            <span class="text-xs text-base-content/50">
              {{ t('settings.lyricsProvider') }}
            </span>
            <span class="text-[10px] text-base-content/40">
              {{ t('settings.lyricsHint') }}
            </span>
          </div>
          <select
            class="select w-full rounded-xl bg-base-100/85 border border-white/10 focus:border-primary/60 disabled:opacity-40"
            v-model="sm.settings.value.lyrics_providers[0]"
            :disabled="!sm.settings.value.download_lyrics"
          >
            <option
              v-for="provider in sm.settingsOptions.lyrics_providers"
              :key="provider"
              :value="provider"
            >
              {{ provider }}
            </option>
          </select>
        </div>

        <!-- Format & bitrate -->
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label
              class="block text-xs font-semibold uppercase tracking-wider text-base-content/50 mb-2"
            >
              {{ t('settings.format') }}
            </label>
            <select
              class="select w-full rounded-xl bg-base-100/85 border border-white/10 focus:border-primary/60"
              v-model="sm.settings.value.format"
            >
              <option
                v-for="fmt in sm.settingsOptions.format"
                :key="fmt"
                :value="fmt"
              >
                {{ fmt.toUpperCase() }}
              </option>
            </select>
          </div>
          <div>
            <div class="flex items-baseline justify-between mb-2">
              <label
                class="block text-xs font-semibold uppercase tracking-wider text-base-content/50"
              >
                {{ t('settings.quality') }}
              </label>
              <span
                v-if="sm.settings.value.format === 'flac'"
                class="text-[10px] text-base-content/40"
              >
                {{ t('settings.qualityIgnored') }}
              </span>
            </div>
            <select
              class="select w-full rounded-xl bg-base-100/85 border border-white/10 focus:border-primary/60"
              v-model="sm.settings.value.bitrate"
              :disabled="sm.settings.value.format === 'flac'"
            >
              <option
                v-for="bitrate in sm.settingsOptions.bitrate"
                :key="bitrate"
                :value="bitrate"
              >
                {{ bitrate }} kbps
              </option>
            </select>
          </div>
        </div>

        <!-- Playlists -->
        <div>
          <label
            class="block text-xs font-semibold uppercase tracking-wider text-base-content/50 mb-2"
          >
            {{ t('settings.playlistsSection') }}
          </label>
          <label
            class="flex items-start gap-3 rounded-xl border border-white/10 bg-base-100/85 px-3 py-2.5 cursor-pointer hover:border-white/20"
          >
            <input
              type="checkbox"
              class="checkbox checkbox-sm checkbox-primary mt-0.5"
              v-model="sm.settings.value.generate_m3u"
            />
            <span class="flex-1 text-sm">
              <span class="block">{{ t('settings.generateM3u') }}</span>
              <span class="block text-[11px] text-base-content/50">
                {{ t('settings.generateM3uHint') }}
              </span>
            </span>
          </label>
        </div>

        <!-- File organization -->
        <div>
          <label
            class="block text-xs font-semibold uppercase tracking-wider text-base-content/50 mb-2"
          >
            {{ t('settings.organizationSection') }}
          </label>
          <div class="space-y-2">
            <label
              class="flex items-start gap-3 rounded-xl border border-white/10 bg-base-100/85 px-3 py-2.5 cursor-pointer hover:border-white/20"
            >
              <input
                type="checkbox"
                class="checkbox checkbox-sm checkbox-primary mt-0.5"
                v-model="sm.settings.value.organize_by_artist"
              />
              <span class="flex-1 text-sm">
                <span class="block">{{ t('settings.organizeByArtist') }}</span>
                <span class="block text-[11px] text-base-content/50">
                  {{ t('settings.organizeByArtistHint') }}
                </span>
              </span>
            </label>
            <label
              class="flex items-start gap-3 rounded-xl border border-white/10 bg-base-100/85 px-3 py-2.5 transition-colors"
              :class="
                sm.settings.value.organize_by_artist
                  ? 'cursor-pointer hover:border-white/20'
                  : 'cursor-not-allowed opacity-50'
              "
            >
              <input
                type="checkbox"
                class="checkbox checkbox-sm checkbox-primary mt-0.5"
                v-model="sm.settings.value.organize_by_album"
                :disabled="!sm.settings.value.organize_by_artist"
              />
              <span class="flex-1 text-sm">
                <span class="block">{{ t('settings.organizeByAlbum') }}</span>
                <span class="block text-[11px] text-base-content/50">
                  {{ t('settings.organizeByAlbumHint') }}
                </span>
              </span>
            </label>
          </div>
        </div>

        <!-- Parallel downloads -->
        <div>
          <label
            class="block text-xs font-semibold uppercase tracking-wider text-base-content/50 mb-2"
          >
            {{ t('settings.parallelDownloads') }}
          </label>
          <div class="grid grid-cols-5 gap-1.5">
            <button
              v-for="n in sm.settingsOptions.max_parallel_downloads"
              :key="n"
              type="button"
              class="rounded-xl border px-2 py-2 text-sm font-medium transition-colors text-center"
              :class="[
                sm.settings.value.max_parallel_downloads === n
                  ? 'border-primary/50 bg-primary/10 text-primary'
                  : 'border-white/10 hover:border-white/20 hover:bg-white/5',
              ]"
              @click="sm.settings.value.max_parallel_downloads = n"
            >
              {{ n }}
            </button>
          </div>
          <p class="text-[11px] text-base-content/40 mt-1.5">
            {{ t('settings.parallelDownloadsHint') }}
          </p>
        </div>

        <!-- Save status -->
        <transition
          enter-active-class="transition duration-200"
          enter-from-class="opacity-0 -translate-y-1"
          enter-to-class="opacity-100 translate-y-0"
          leave-active-class="transition duration-200"
          leave-from-class="opacity-100"
          leave-to-class="opacity-0"
        >
          <div
            v-if="sm.isSaved.value === true"
            class="surface rounded-xl p-3 flex items-center gap-2 text-sm text-primary"
          >
            <Icon icon="clarity:check-line" class="h-4 w-4 shrink-0" />
            {{ t('settings.saved') }}
          </div>
          <div
            v-else-if="sm.isSaved.value === false"
            class="surface rounded-xl p-3 flex items-center gap-2 text-sm text-error"
          >
            <Icon
              icon="clarity:exclamation-circle-line"
              class="h-4 w-4 shrink-0"
            />
            {{ t('settings.saveError') }}
          </div>
        </transition>
      </div>

      <!-- Footer -->
      <div
        class="flex items-center justify-end gap-2 px-6 py-4 border-t border-white/5"
      >
        <label
          for="settings-modal"
          class="btn btn-sm h-10 px-5 rounded-full border-white/10 bg-base-100/85 hover:bg-base-100 cursor-pointer"
        >
          {{ t('common.cancel') }}
        </label>
        <button
          class="btn btn-primary btn-sm h-10 px-6 rounded-full"
          @click="sm.saveSettings()"
        >
          {{ t('common.save') }}
        </button>
      </div>
    </div>
    <label class="modal-backdrop" for="settings-modal">{{
      t('common.close')
    }}</label>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Icon } from '@iconify/vue'
import { useSettingsManager } from '../model/settings'
import { useDownloadDestination } from '../model/downloadDestination'
import { useI18n } from '../i18n'

const sm = useSettingsManager()
const {
  destination,
  localFolderName,
  localFolderReady,
  localFolderBlockReason,
  usesBrowserDownloads,
  isLocal,
  setDestination,
  pickLocalFolder,
  activateLocalDestination,
} = useDownloadDestination()
const { t, locale, setLocale, locales } = useI18n()
const folderPickerError = ref('')

const localFolderBlockMessage = computed(() => {
  if (localFolderBlockReason.value === 'insecure') {
    return t('settings.localFolderInsecure')
  }
  if (localFolderBlockReason.value === 'browser') {
    return t('settings.localFolderUnsupported')
  }
  return ''
})

const localDestinationHint = computed(() =>
  usesBrowserDownloads.value
    ? t('settings.downloadDestinationBrowserHint')
    : t('settings.downloadDestinationLocalHint')
)

function localFolderErrorMessage(reason) {
  if (reason === 'insecure') return t('settings.localFolderInsecure')
  if (reason === 'browser') return t('settings.localFolderUnsupported')
  return t('settings.localFolderError')
}

function providerLabel(provider) {
  if (provider === 'youtube-music') return 'YouTube Music'
  if (provider === 'youtube') return 'YouTube'
  return provider
}

async function selectLocalDestination() {
  if (isLocal.value && localFolderName.value) return

  folderPickerError.value = ''
  try {
    await activateLocalDestination()
  } catch (err) {
    if (err?.name === 'AbortError') return
    if (['insecure', 'browser', 'unsupported', 'unavailable'].includes(err?.message)) {
      folderPickerError.value = localFolderErrorMessage(err.message)
      return
    }
    folderPickerError.value = err?.message || t('settings.localFolderError')
  }
}

async function changeLocalFolder() {
  folderPickerError.value = ''
  try {
    await pickLocalFolder()
    setDestination('local')
  } catch (err) {
    if (err?.name === 'AbortError') return
    if (['insecure', 'browser', 'unsupported', 'unavailable'].includes(err?.message)) {
      folderPickerError.value = localFolderErrorMessage(err.message)
      return
    }
    folderPickerError.value = err?.message || t('settings.localFolderError')
  }
}
</script>
