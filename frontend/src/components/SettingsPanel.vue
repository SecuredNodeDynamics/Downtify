<template>
  <div
    class="settings-panel surface-strong rounded-2xl sm:rounded-3xl overflow-x-hidden"
  >
    <!-- Tabs -->
    <div class="settings-tabs-wrap px-4 sm:px-6">
      <div
        ref="tabShellRef"
        class="settings-tab-shell tab-glow-shell"
        role="tablist"
        :aria-label="t('settings.title')"
      >
        <button
          v-for="tab in settingsTabs"
          :key="tab.id"
          type="button"
          role="tab"
          class="settings-tab-btn"
          :class="{ 'settings-tab-btn-active': activeTab === tab.id }"
          :aria-selected="activeTab === tab.id"
          @click="setActiveTab(tab.id)"
        >
          {{ t(tab.labelKey) }}
        </button>
      </div>
    </div>

    <div v-if="activeTab === 'general'" class="px-4 pb-5 space-y-6 sm:px-6">
      <!-- App mode: on-device (serverless) vs remote server -->
      <div v-if="embeddedAvailable">
        <label
          class="block text-xs font-semibold uppercase tracking-wider text-base-content/50 mb-2"
        >
          {{ t('settings.modeSection') }}
        </label>
        <div class="grid grid-cols-2 gap-2">
          <button
            type="button"
            class="rounded-xl border px-3 py-2 text-sm transition-colors text-left"
            :class="[
              isDeviceMode
                ? 'border-primary/50 bg-primary/10 text-primary'
                : 'border-white/10 hover:border-white/20 hover:bg-white/5',
            ]"
            @click="selectConnectionMode('device')"
          >
            {{ t('settings.connectionModeDevice') }}
          </button>
          <button
            type="button"
            class="rounded-xl border px-3 py-2 text-sm transition-colors text-left"
            :class="[
              !isDeviceMode
                ? 'border-primary/50 bg-primary/10 text-primary'
                : 'border-white/10 hover:border-white/20 hover:bg-white/5',
            ]"
            @click="selectConnectionMode('server')"
          >
            {{ t('settings.connectionModeServer') }}
          </button>
        </div>
        <p class="text-[11px] text-base-content/40 mt-1.5">
          {{
            isDeviceMode
              ? t('settings.connectionModeDeviceHint')
              : t('settings.connectionModeServerHint')
          }}
        </p>
        <p v-if="!isDeviceMode" class="text-[11px] text-base-content/40 mt-1">
          {{ t('settings.connectionModeServerConfigHint') }}
        </p>
      </div>

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

      <!-- Download destination (irrelevant in on-device mode: files are
           always saved locally by the embedded backend). -->
      <div v-if="!isDeviceMode">
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
        <div v-if="destination === 'server'" class="mt-3">
          <label class="block text-xs text-base-content/50 mb-1.5">
            {{ t('settings.serverMediaLocation') }}
          </label>
          <input
            v-model="sm.settings.value.server_media_location"
            type="text"
            class="input-modern h-10 w-full text-sm"
            :placeholder="t('settings.serverMediaLocationPlaceholder')"
          />
          <p class="text-[11px] text-base-content/40 mt-1.5">
            {{ t('settings.serverMediaLocationHint') }}
          </p>
        </div>
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
                {{ localFolderName || t('settings.localFolderNone') }}
              </p>
              <p class="mt-1 text-[11px] text-base-content/40">
                {{ localFolderDetailHint }}
              </p>
            </div>
          </div>
          <div
            v-if="!usesBrowserDownloads"
            class="flex flex-wrap items-center gap-2"
          >
            <button
              type="button"
              class="btn btn-sm h-9 rounded-full border-white/10 bg-base-100/85 hover:bg-base-100"
              @click="changeLocalFolder"
            >
              {{ t('settings.changeLocalFolder') }}
            </button>
          </div>
          <p
            v-if="!localFolderReady && !usesNativeDownloads"
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

      <!-- Metadata -->
      <div>
        <label
          class="block text-xs font-semibold uppercase tracking-wider text-base-content/50 mb-2"
        >
          {{ t('settings.metadataSection') }}
        </label>
        <label
          class="flex items-start gap-3 rounded-xl border border-white/10 bg-base-100/85 px-3 py-2.5 cursor-pointer hover:border-white/20"
        >
          <input
            type="checkbox"
            class="checkbox checkbox-sm checkbox-primary mt-0.5"
            v-model="sm.settings.value.enhance_metadata"
          />
          <span class="flex-1 text-sm">
            <span class="block">{{ t('settings.enhanceMetadata') }}</span>
            <span class="block text-[11px] text-base-content/50">
              {{ t('settings.enhanceMetadataHint') }}
            </span>
          </span>
        </label>
        <label class="mt-3 block text-xs text-base-content/55">
          <span class="mb-1 block font-semibold text-base-content/70">
            {{ t('settings.artistFolderPolicy') }}
          </span>
          <select
            class="select h-10 w-full rounded-xl border-white/10 bg-base-100/85 text-sm"
            v-model="sm.settings.value.artist_folder_policy"
          >
            <option value="artwork_available">
              {{ t('settings.artistFolderPolicyArtwork') }}
            </option>
            <option value="primary_only">
              {{ t('settings.artistFolderPolicyPrimary') }}
            </option>
            <option value="existing_only">
              {{ t('settings.artistFolderPolicyExisting') }}
            </option>
          </select>
          <span class="mt-1 block text-[11px] text-base-content/50">
            {{ t('settings.artistFolderPolicyHint') }}
          </span>
        </label>
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
        <div class="grid grid-cols-3 gap-1.5 sm:grid-cols-6">
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

    <div v-else-if="activeTab === 'api'" class="px-4 pb-5 space-y-5 sm:px-6">
      <div>
        <label
          class="block text-xs font-semibold uppercase tracking-wider text-base-content/50 mb-2"
        >
          {{ t('settings.serverConnectionSection') }}
        </label>
        <p class="mb-3 text-sm text-base-content/60">
          {{ t('settings.serverConnectionHint') }}
        </p>

        <div
          v-if="isDeviceMode"
          class="flex items-start gap-3 rounded-xl border border-primary/30 bg-primary/10 px-3 py-3"
        >
          <Icon
            icon="clarity:mobile-line"
            class="mt-0.5 h-5 w-5 shrink-0 text-primary"
          />
          <div class="min-w-0">
            <p class="text-sm font-medium text-primary">
              {{ t('settings.runningOnThisDevice') }}
            </p>
            <p class="mt-1 text-[11px] text-base-content/50">
              {{ t('settings.runningOnThisDeviceSwitchHint') }}
            </p>
          </div>
        </div>

        <div v-else class="space-y-3">
          <div class="surface rounded-xl px-3 py-2.5 text-sm">
            <span class="text-base-content/50">
              {{ t('settings.serverUrlCurrent') }}:
            </span>
            <span class="ml-1 font-medium text-base-content">
              {{
                usesCustomServer
                  ? activeServerDisplay
                  : t('settings.serverUrlDefault')
              }}
            </span>
          </div>
          <div>
            <label class="block text-xs text-base-content/50 mb-1.5">
              {{ t('settings.serverUrl') }}
            </label>
            <input
              v-model="serverUrlInput"
              type="url"
              inputmode="url"
              autocapitalize="off"
              autocorrect="off"
              spellcheck="false"
              class="input-modern h-10 w-full text-sm"
              :placeholder="t('settings.serverUrlPlaceholder')"
            />
            <p class="text-[11px] text-base-content/40 mt-1.5">
              {{ t('settings.serverSaveHint') }}
            </p>
          </div>
          <div class="flex flex-col gap-2 sm:flex-row sm:flex-wrap">
            <button
              v-if="canConnectDevice"
              type="button"
              class="btn btn-primary btn-sm h-10 w-full rounded-full px-4 sm:w-auto"
              :disabled="connectedToThisDevice || serverTestLoading"
              @click="connectToThisDevice"
            >
              {{ t('settings.serverConnectDevice') }}
            </button>
            <button
              type="button"
              class="btn btn-sm h-10 w-full rounded-full px-4 sm:w-auto"
              :class="
                canConnectDevice
                  ? 'border border-white/10 bg-base-100/85 text-base-content hover:bg-base-100'
                  : 'btn-primary'
              "
              :disabled="serverTestLoading || !serverUrlInput.trim()"
              @click="testServerConnection"
            >
              <span
                v-if="serverTestLoading"
                class="loading loading-spinner loading-xs mr-2"
              />
              {{
                serverTestLoading
                  ? t('settings.serverTesting')
                  : t('settings.serverTest')
              }}
            </button>
            <button
              type="button"
              class="btn btn-sm h-10 w-full rounded-full border border-white/10 bg-base-100/85 px-4 text-base-content hover:bg-base-100 sm:w-auto"
              :disabled="!canSaveServerUrl || serverTestLoading"
              @click="saveServerConnection"
            >
              {{ t('settings.serverSave') }}
            </button>
            <button
              v-if="usesCustomServer && !connectedToThisDevice"
              type="button"
              class="btn btn-sm h-10 w-full rounded-full border border-white/10 bg-base-100/85 px-4 text-base-content hover:bg-base-100 sm:w-auto"
              @click="resetServerConnection"
            >
              {{ t('settings.serverClear') }}
            </button>
          </div>
          <p
            v-if="serverTestMessage"
            class="text-[11px]"
            :class="serverTestError ? 'text-error' : 'text-primary'"
          >
            {{ serverTestMessage }}
          </p>
        </div>
      </div>

      <div>
        <label
          class="block text-xs font-semibold uppercase tracking-wider text-base-content/50 mb-2"
        >
          {{ t('settings.jellyfinSection') }}
        </label>
        <div class="space-y-3">
          <label
            class="flex items-start gap-3 rounded-xl border border-white/10 bg-base-100/85 px-3 py-2.5 cursor-pointer hover:border-white/20"
          >
            <input
              type="checkbox"
              class="checkbox checkbox-sm checkbox-primary mt-0.5"
              v-model="sm.settings.value.enable_jellyfin_tools"
            />
            <span class="flex-1 text-sm">
              <span class="block">{{ t('settings.enableJellyfinTools') }}</span>
              <span class="block text-[11px] text-base-content/50">
                {{ t('settings.enableJellyfinToolsHint') }}
              </span>
            </span>
          </label>
          <div>
            <label class="block text-xs text-base-content/50 mb-1.5">
              {{ t('settings.jellyfinUrl') }}
            </label>
            <input
              v-model="sm.settings.value.jellyfin_url"
              type="url"
              class="input-modern h-10 w-full text-sm"
              :placeholder="t('settings.jellyfinUrlPlaceholder')"
              @change="onJellyfinConfigChange"
            />
            <p
              class="mt-1.5 text-center text-[11px] leading-snug text-base-content/40"
            >
              {{ t('settings.jellyfinUrlHint') }}
            </p>
          </div>
          <div>
            <label class="block text-xs text-base-content/50 mb-1.5">
              {{ t('settings.jellyfinApiKey') }}
            </label>
            <div class="flex items-start gap-2">
              <div class="flex min-w-0 flex-1 flex-col">
                <input
                  v-model="sm.settings.value.jellyfin_api_key"
                  type="password"
                  autocomplete="off"
                  class="input-modern h-10 w-full text-sm"
                  :placeholder="t('settings.jellyfinApiKeyPlaceholder')"
                  @change="onJellyfinConfigChange"
                />
                <p
                  class="mt-1.5 text-center text-[11px] leading-snug text-base-content/40"
                >
                  {{ t('settings.jellyfinApiKeyHint') }}
                </p>
              </div>
              <button
                type="button"
                class="btn btn-sm h-10 shrink-0 px-3 rounded-lg border-white/10 bg-base-100/85 hover:bg-base-100"
                :disabled="
                  jellyfinTestLoading ||
                  !sm.settings.value.jellyfin_url?.trim() ||
                  !sm.settings.value.jellyfin_api_key?.trim()
                "
                @click="testJellyfinApi"
              >
                <span
                  v-if="jellyfinTestLoading"
                  class="loading loading-spinner loading-xs"
                ></span>
                {{
                  jellyfinTestLoading
                    ? t('settings.jellyfinTesting')
                    : t('settings.jellyfinTest')
                }}
              </button>
            </div>
            <p
              v-if="jellyfinTestMessage"
              class="mt-1.5 text-center text-[11px]"
              :class="jellyfinTestError ? 'text-error' : 'text-primary'"
            >
              {{ jellyfinTestMessage }}
            </p>
          </div>
          <div>
            <label class="block text-xs text-base-content/50 mb-1.5">
              {{ t('settings.jellyfinMusicLibrary') }}
            </label>
            <div v-if="jellyfinLibraryLoading" class="flex flex-col">
              <div
                class="h-10 w-full rounded-xl bg-base-100/85 border border-white/10 flex items-center px-3"
              >
                <span class="text-sm text-base-content/60">{{
                  t('settings.jellyfinLibraryLoading')
                }}</span>
              </div>
              <p
                class="mt-1.5 text-center text-[11px] leading-snug text-base-content/40"
              >
                {{ t('settings.jellyfinMusicLibraryHint') }}
              </p>
            </div>
            <div v-else-if="jellyfinLibraryError" class="space-y-1.5">
              <div class="flex items-start gap-2">
                <div class="flex min-w-0 flex-1 flex-col">
                  <ThemedSelect
                    v-model="sm.settings.value.jellyfin_music_library"
                    :options="jellyfinLibraryOptions"
                    :placeholder="t('settings.jellyfinMusicLibraryPlaceholder')"
                    disabled
                  />
                  <p
                    class="mt-1.5 text-center text-[11px] leading-snug text-base-content/40"
                  >
                    {{ t('settings.jellyfinMusicLibraryHint') }}
                  </p>
                </div>
                <button
                  type="button"
                  class="btn btn-sm h-10 shrink-0 px-3 rounded-lg border-white/10 bg-base-100/85 hover:bg-base-100"
                  @click="onJellyfinConfigChange"
                  :disabled="jellyfinLibraryLoading"
                >
                  {{ t('common.refresh') }}
                </button>
              </div>
              <p class="text-[11px] text-error">{{ jellyfinLibraryError }}</p>
            </div>
            <div v-else class="flex items-start gap-2">
              <div class="flex min-w-0 flex-1 flex-col">
                <ThemedSelect
                  v-model="sm.settings.value.jellyfin_music_library"
                  :options="jellyfinLibraryOptions"
                  :placeholder="t('settings.jellyfinMusicLibraryPlaceholder')"
                  :disabled="uniqueJellyfinLibraries.length === 0"
                />
                <p
                  class="mt-1.5 text-center text-[11px] leading-snug text-base-content/40"
                >
                  {{ t('settings.jellyfinMusicLibraryHint') }}
                </p>
              </div>
              <button
                type="button"
                class="btn btn-sm h-10 shrink-0 px-3 rounded-lg border-white/10 bg-base-100/85 hover:bg-base-100"
                @click="onJellyfinConfigChange"
                :disabled="jellyfinLibraryLoading"
              >
                {{ t('common.refresh') }}
              </button>
            </div>
          </div>
        </div>
      </div>

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

    <div v-else-if="activeTab === 'logs'" class="px-4 pb-5 space-y-5 sm:px-6">
      <div class="flex items-center justify-between gap-3">
        <div>
          <label
            class="block text-xs font-semibold uppercase tracking-wider text-base-content/50"
          >
            {{ t('metadata.repairLog') }}
          </label>
          <p class="mt-1 text-[11px] text-base-content/45">
            {{ t('settings.logsHint') }}
          </p>
        </div>
        <button
          type="button"
          class="btn btn-sm h-9 rounded-full border-white/10 bg-base-100/85 hover:bg-base-100"
          :disabled="repairLogLoading"
          @click="loadRepairLog"
        >
          <span
            v-if="repairLogLoading"
            class="loading loading-spinner loading-xs mr-2"
          />
          <Icon v-else icon="clarity:refresh-line" class="h-4 w-4 mr-2" />
          {{ t('common.refresh') }}
        </button>
      </div>

      <div
        v-if="repairLogError"
        class="surface rounded-xl p-3 flex items-center gap-2 text-sm text-error"
      >
        <Icon icon="clarity:exclamation-circle-line" class="h-4 w-4 shrink-0" />
        {{ repairLogError }}
      </div>

      <div
        v-if="repairLog.length === 0 && !repairLogLoading"
        class="surface rounded-2xl p-8 text-center text-sm text-base-content/50"
      >
        <Icon
          icon="clarity:history-line"
          class="mx-auto mb-3 h-9 w-9 text-base-content/20"
        />
        {{ t('metadata.emptyRepairLog') }}
      </div>

      <ul v-else class="max-h-[24rem] space-y-3 overflow-y-auto pr-1">
        <li
          v-for="entry in repairLog"
          :key="`${entry.created_at}-${entry.kind}-${entry.target}`"
          class="surface rounded-2xl p-4"
        >
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0">
              <p class="truncate text-sm font-semibold">
                {{ entry.target }}
              </p>
              <p class="mt-1 text-xs text-base-content/45">
                {{ logKindLabel(entry.kind) }} ·
                {{ entry.detail || entry.created_at }}
              </p>
            </div>
            <span
              class="pill shrink-0"
              :class="
                entry.status === 'success'
                  ? 'badge-soft'
                  : 'bg-error/10 text-error'
              "
            >
              {{ entry.status }}
            </span>
          </div>
        </li>
      </ul>
    </div>

    <div v-else-if="activeTab === 'about'" class="px-4 pb-5 space-y-5 sm:px-6">
      <div>
        <label
          class="block text-xs font-semibold uppercase tracking-wider text-base-content/50"
        >
          {{ t('settings.aboutTitle') }}
        </label>
        <p class="mt-1 text-sm text-base-content/60">
          {{ t('settings.aboutSubtitle') }}
        </p>
      </div>

      <div class="grid gap-3 md:grid-cols-2">
        <div
          v-for="section in aboutSections"
          :key="section.title"
          class="surface rounded-2xl p-4"
        >
          <div class="flex items-start gap-3">
            <Icon
              :icon="section.icon"
              class="mt-0.5 h-5 w-5 shrink-0 text-primary"
            />
            <div class="min-w-0">
              <p class="text-sm font-semibold">
                {{ section.title }}
              </p>
              <p class="mt-1 text-xs leading-relaxed text-base-content/55">
                {{ section.text }}
              </p>
            </div>
          </div>
        </div>
      </div>

      <div class="surface rounded-2xl p-4">
        <div class="flex items-start gap-3">
          <Icon
            icon="clarity:flow-chart-line"
            class="mt-0.5 h-5 w-5 shrink-0 text-primary"
          />
          <div>
            <p class="text-sm font-semibold">
              {{ t('settings.aboutWorkflowTitle') }}
            </p>
            <p class="mt-1 text-xs leading-relaxed text-base-content/55">
              {{ t('settings.aboutWorkflowText') }}
            </p>
          </div>
        </div>
      </div>
    </div>

    <div v-else-if="activeTab === 'help'" class="px-4 pb-5 space-y-5 sm:px-6">
      <div class="flex items-start justify-between gap-3">
        <div>
          <label
            class="block text-xs font-semibold uppercase tracking-wider text-base-content/50"
          >
            {{ t('settings.helpTitle') }}
          </label>
          <p class="mt-1 text-sm text-base-content/60">
            {{ t('settings.helpSubtitle') }}
          </p>
        </div>
        <button
          type="button"
          class="btn btn-sm h-9 rounded-full border-white/10 bg-base-100/85 hover:bg-base-100"
          :disabled="helpLoading"
          @click="loadUpdateStatus(true)"
        >
          <span
            v-if="helpLoading"
            class="loading loading-spinner loading-xs mr-2"
          />
          <Icon v-else icon="clarity:refresh-line" class="h-4 w-4 mr-2" />
          {{ t('settings.checkUpdates') }}
        </button>
      </div>

      <div class="grid gap-3 md:grid-cols-2">
        <div class="surface rounded-2xl p-4">
          <p class="text-xs uppercase tracking-wider text-base-content/45">
            {{ t('settings.currentVersion') }}
          </p>
          <p class="mt-2 text-2xl font-bold text-base-content">
            v{{ currentAppVersion }}
          </p>
        </div>
        <div class="surface rounded-2xl p-4">
          <p class="text-xs uppercase tracking-wider text-base-content/45">
            {{ t('settings.latestVersion') }}
          </p>
          <p class="mt-2 text-2xl font-bold text-base-content">
            {{ latestVersionLabel }}
          </p>
        </div>
      </div>

      <div
        v-if="versionMismatch"
        class="surface rounded-xl border border-warning/30 bg-warning/10 p-3 flex gap-3 items-start text-sm text-warning"
      >
        <Icon icon="clarity:warning-standard-line" class="h-5 w-5 shrink-0" />
        <span>{{ versionMismatchMessage }}</span>
      </div>

      <div
        v-if="helpError"
        class="surface rounded-xl p-3 flex items-center gap-2 text-sm text-error"
      >
        <Icon icon="clarity:exclamation-circle-line" class="h-4 w-4 shrink-0" />
        {{ helpError }}
      </div>

      <div class="surface rounded-2xl p-4">
        <div class="flex items-start gap-3">
          <Icon
            :icon="updateStatusIcon"
            class="mt-0.5 h-5 w-5 shrink-0 text-primary"
          />
          <div class="min-w-0 flex-1">
            <p class="text-sm font-semibold">
              {{ updateStatusTitle }}
            </p>
            <p class="mt-1 text-xs leading-relaxed text-base-content/55">
              {{ updateStatusMessage }}
            </p>
            <a
              v-if="updateStatus?.release_url"
              :href="updateStatus.release_url"
              target="_blank"
              rel="noreferrer"
              class="mt-2 inline-flex text-xs font-medium text-primary hover:text-primary-focus"
            >
              {{ t('settings.viewRelease') }}
            </a>
          </div>
        </div>
      </div>

      <div class="flex flex-wrap items-center gap-2">
        <button
          v-if="!updateRunning"
          type="button"
          class="btn btn-primary btn-sm h-10 rounded-full px-5"
          :disabled="!canRunUpdate"
          @click="runUpdate"
        >
          <Icon icon="clarity:download-cloud-line" class="h-4 w-4 mr-2" />
          {{ t('settings.updateApp') }}
        </button>
        <p class="text-xs text-base-content/45">
          {{ updateHintText }}
        </p>
      </div>

      <div
        v-if="updateWaiting"
        class="surface rounded-2xl border border-primary/30 bg-primary/10 p-5"
      >
        <div class="flex items-start gap-3">
          <span
            class="loading loading-spinner loading-md shrink-0 text-primary mt-0.5"
          />
          <div class="min-w-0">
            <p class="font-semibold text-primary">
              {{ t('settings.updateInProgress') }}
            </p>
            <p class="mt-1 text-sm text-base-content/70">
              {{ updateInProgressHintText }}
            </p>
          </div>
        </div>
      </div>

      <div
        v-if="updateFailed"
        class="surface rounded-2xl border border-error/30 bg-error/10 p-5"
      >
        <div class="flex items-start gap-3">
          <Icon
            icon="clarity:exclamation-circle-line"
            class="mt-0.5 h-6 w-6 shrink-0 text-error"
          />
          <div class="min-w-0">
            <p class="font-semibold text-error">
              {{ t('settings.updateFailed') }}
            </p>
            <p class="mt-1 text-sm text-base-content/70">
              {{ updateFailureMessage }}
            </p>
          </div>
        </div>
      </div>

      <div
        v-if="updateCompleted"
        class="surface rounded-2xl border border-success/30 bg-success/10 p-5"
      >
        <div class="flex items-start gap-3">
          <Icon
            icon="clarity:success-standard-line"
            class="mt-0.5 h-6 w-6 shrink-0 text-success"
          />
          <div>
            <p class="font-semibold text-success">
              {{ t('settings.updateFinished') }}
            </p>
            <p class="mt-1 text-sm text-base-content/70">
              {{ t('settings.refreshAfterUpdate') }}
            </p>
            <button
              type="button"
              class="btn btn-success btn-sm mt-4 h-10 rounded-full px-5"
              @click="refreshPage"
            >
              <Icon icon="clarity:refresh-line" class="mr-2 h-4 w-4" />
              {{ t('settings.refreshPage') }}
            </button>
          </div>
        </div>
      </div>

      <div
        v-if="
          updateResult && !updateCompleted && !updateWaiting && !updateFailed
        "
        class="surface rounded-2xl p-4"
        :class="updateResult.success ? 'text-base-content' : 'text-error'"
      >
        <p class="text-sm font-semibold">
          {{ updateResult.message || t('settings.updateFinished') }}
        </p>
        <p
          v-if="updateResult.requires_restart"
          class="mt-1 text-xs text-base-content/55"
        >
          {{ t('settings.restartRequired') }}
        </p>
        <p
          v-if="updateResult.restart_scheduled"
          class="mt-1 text-xs text-success"
        >
          {{ t('settings.restartScheduled') }}
        </p>
        <div v-if="updateResult.commands?.length" class="mt-3 space-y-2">
          <p class="text-xs text-base-content/55">
            {{ t('settings.manualUpdateCommands') }}
          </p>
          <code
            v-for="command in updateResult.commands"
            :key="command"
            class="block rounded-lg border border-white/10 bg-black/30 px-3 py-2 text-xs text-base-content"
          >
            {{ command }}
          </code>
        </div>
        <pre
          v-if="updateResult.terminal_output || updateResult.pull_output"
          class="mt-3 max-h-40 overflow-auto rounded-xl border border-white/10 bg-black/30 p-3 text-xs text-base-content/70"
          >{{ updateResult.terminal_output || updateResult.pull_output }}</pre
        >
      </div>
    </div>

    <!-- Footer -->
    <div
      class="flex items-center justify-end gap-2 px-4 py-4 border-t border-white/5 sm:px-6"
    >
      <button
        class="btn btn-primary btn-sm h-10 px-6 rounded-full"
        @click="sm.saveSettings()"
      >
        {{ t('common.save') }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { Icon } from '@iconify/vue'
import axios from 'axios'
import { useSettingsManager } from '../model/settings'
import { useDownloadDestination } from '../model/downloadDestination'
import {
  buildApiBaseUrl,
  canConnectToCurrentPage,
  canSaveServerUrlInput,
  formatServerDisplay,
  getConnectionMode,
  getCurrentPageServerUrl,
  getServerConfig,
  getStoredServerUrl,
  isCapacitorNative,
  isConnectedToCurrentPage,
  isEmbeddedServerAvailable,
  parseServerUrl,
  setConnectionMode,
  setStoredServerUrl,
  usesCustomServerUrl,
} from '../model/serverConnection'
import { useI18n } from '../i18n'
import API from '../model/api'
import { usesApkUpdateFlow } from '../model/appUpdate'
import {
  checkDowntifyVersion,
  getCachedUpdateStatus,
} from '../model/appVersion'
import { installApkUpdate } from '../model/apkUpdate'
import ThemedSelect from './ThemedSelect.vue'

const route = useRoute()

const sm = useSettingsManager()
const {
  destination,
  localFolderName,
  localFolderReady,
  localFolderBlockReason,
  usesBrowserDownloads,
  usesNativeDownloads,
  isLocal,
  setDestination,
  pickLocalFolder,
  activateLocalDestination,
} = useDownloadDestination()
const { t, locale, setLocale, locales } = useI18n()
const folderPickerError = ref('')
const activeTab = ref('general')
const tabShellRef = ref(null)

const settingsTabs = [
  { id: 'general', labelKey: 'settings.generalTab' },
  { id: 'api', labelKey: 'settings.apiTab' },
  { id: 'logs', labelKey: 'settings.logsTab' },
  { id: 'about', labelKey: 'settings.aboutTab' },
  { id: 'help', labelKey: 'settings.helpTab' },
]

function scrollActiveTabIntoView() {
  const shell = tabShellRef.value
  if (!shell) return
  const selected = shell.querySelector('[aria-selected="true"]')
  selected?.scrollIntoView({
    inline: 'center',
    block: 'nearest',
    behavior: 'smooth',
  })
}

function setActiveTab(tab) {
  if (!settingsTabs.some((item) => item.id === tab)) return
  activeTab.value = tab
  nextTick(scrollActiveTabIntoView)
}
const jellyfinLibraries = ref([])
const jellyfinLibraryLoading = ref(false)
const jellyfinLibraryError = ref('')
const jellyfinTestLoading = ref(false)
const jellyfinTestMessage = ref('')
const jellyfinTestError = ref(false)
const serverUrlInput = ref(getStoredServerUrl())
const serverTestLoading = ref(false)
const serverTestMessage = ref('')
const serverTestError = ref(false)
const usesCustomServer = computed(() => usesCustomServerUrl())
const embeddedAvailable = computed(() => isEmbeddedServerAvailable())
const connectionMode = ref(getConnectionMode())
const isDeviceMode = computed(
  () => embeddedAvailable.value && connectionMode.value === 'device'
)
const activeServerDisplay = computed(() =>
  formatServerDisplay(getServerConfig())
)
const canConnectDevice = computed(() => canConnectToCurrentPage())
const connectedToThisDevice = computed(() => isConnectedToCurrentPage())
const canSaveServerUrl = computed(() =>
  canSaveServerUrlInput(serverUrlInput.value)
)
const repairLog = ref([])
const repairLogLoading = ref(false)
const repairLogError = ref('')
const updateStatus = ref(null)
const helpLoading = ref(false)
const helpError = ref('')
const updateRunning = ref(false)
const updateWaiting = ref(false)
const updateFailed = ref(false)
const updateFailureMessage = ref('')
const updateResult = ref(null)
const updateCompleted = ref(false)
let updateCompletionTimer = null

function clearUpdateTimers() {
  clearTimeout(updateCompletionTimer)
  updateCompletionTimer = null
}

function resetUpdateFeedback() {
  updateFailed.value = false
  updateFailureMessage.value = ''
  updateResult.value = null
  updateCompleted.value = false
}

function markUpdateFailed(message) {
  updateWaiting.value = false
  updateRunning.value = false
  updateFailed.value = true
  updateFailureMessage.value = message || t('settings.updateFailed')
}

function applySettingsTab(tab) {
  if (settingsTabs.some((item) => item.id === tab)) {
    setActiveTab(tab)
  }
}

function openSettingsTab(event) {
  applySettingsTab(event?.detail?.tab)
}

onMounted(() =>
  window.addEventListener('downtify:open-settings', openSettingsTab)
)
onBeforeUnmount(() =>
  window.removeEventListener('downtify:open-settings', openSettingsTab)
)
onBeforeUnmount(() => clearUpdateTimers())
function normalizedJellyfinLibraryName(value) {
  return String(value || '')
    .normalize('NFKC')
    .replace(
      /[\u0000-\u001f\u007f-\u009f\u200b-\u200f\u202a-\u202e\u2060-\u206f\ufeff]/g,
      ''
    )
    .replace(/\s+/g, ' ')
    .trim()
    .toLowerCase()
}

const uniqueJellyfinLibraries = computed(() => {
  return uniqueLibrariesByName(jellyfinLibraries.value)
})

const jellyfinLibraryOptions = computed(() =>
  uniqueJellyfinLibraries.value.map((lib) => ({
    value: lib.name,
    label: lib.display_name || lib.name,
  }))
)

const aboutSections = computed(() => [
  {
    icon: 'clarity:search-line',
    title: t('settings.aboutSearchTitle'),
    text: t('settings.aboutSearchText'),
  },
  {
    icon: 'clarity:library-line',
    title: t('settings.aboutLibraryTitle'),
    text: t('settings.aboutLibraryText'),
  },
  {
    icon: 'clarity:download-line',
    title: t('settings.aboutQueueTitle'),
    text: t('settings.aboutQueueText'),
  },
  {
    icon: 'clarity:headphones-line',
    title: t('settings.aboutPlayerTitle'),
    text: t('settings.aboutPlayerText'),
  },
  {
    icon: 'clarity:eye-line',
    title: t('settings.aboutMonitorTitle'),
    text: t('settings.aboutMonitorText'),
  },
  {
    icon: 'clarity:tag-line',
    title: t('settings.aboutMetadataTitle'),
    text: t('settings.aboutMetadataText'),
  },
  {
    icon: 'clarity:image-gallery-line',
    title: t('settings.aboutArtistImagesTitle'),
    text: t('settings.aboutArtistImagesText'),
  },
  {
    icon: 'clarity:server-line',
    title: t('settings.aboutJellyfinTitle'),
    text: t('settings.aboutJellyfinText'),
  },
  {
    icon: 'clarity:info-standard-line',
    title: t('settings.aboutHealthTitle'),
    text: t('settings.aboutHealthText'),
  },
  {
    icon: 'clarity:cog-line',
    title: t('settings.aboutSettingsTitle'),
    text: t('settings.aboutSettingsText'),
  },
])

const currentAppVersion = computed(() => {
  const version = updateStatus.value?.current_version
  return version || t('settings.unknownVersion')
})

const versionMismatch = computed(() =>
  Boolean(updateStatus.value?.version_mismatch)
)

const versionMismatchMessage = computed(() => {
  const status = updateStatus.value
  if (!status?.version_mismatch) return ''
  return t('settings.versionMismatchHint', {
    app: status.current_version,
    server: status.connected_server_version,
    latest: status.latest_version || status.connected_server_version,
  })
})

const latestVersionLabel = computed(() => {
  if (helpLoading.value && !updateStatus.value) return t('settings.checking')
  const latest = updateStatus.value?.latest_version
  return latest ? `v${latest}` : t('settings.unknownVersion')
})

const canRunUpdate = computed(() => {
  if (usesApkUpdateFlow()) {
    return Boolean(
      updateStatus.value?.needs_apk_update &&
        updateStatus.value?.apk_download_url
    )
  }
  return Boolean(updateStatus.value?.update_available)
})

const updateHintText = computed(() => {
  if (usesApkUpdateFlow()) {
    if (updateStatus.value?.needs_server_update) {
      return t('settings.updateHintServerBehind')
    }
    return t('settings.updateHintApk')
  }
  return t('settings.updateHint')
})

const updateInProgressHintText = computed(() =>
  usesApkUpdateFlow()
    ? t('settings.updateInProgressHintApk')
    : t('settings.updateInProgressHint')
)

const updateStatusIcon = computed(() => {
  if (helpLoading.value) return 'clarity:refresh-line'
  if (updateStatus.value?.update_available) return 'clarity:download-cloud-line'
  if (helpError.value || updateStatus.value?.error) {
    return 'clarity:exclamation-circle-line'
  }
  return 'clarity:check-circle-line'
})

const updateStatusTitle = computed(() => {
  if (helpLoading.value) return t('settings.checkingUpdates')
  if (updateStatus.value?.update_available) {
    return t('settings.updateAvailable')
  }
  if (helpError.value || updateStatus.value?.error) {
    return t('settings.updateCheckFailed')
  }
  return t('settings.upToDate')
})

const updateStatusMessage = computed(() => {
  if (helpLoading.value) return t('settings.checkingUpdatesHint')
  if (updateStatus.value?.update_available) {
    return t('settings.updateAvailableHint', {
      version: updateStatus.value.latest_version,
    })
  }
  if (updateStatus.value?.error) return updateStatus.value.error
  return t('settings.upToDateHint')
})

function uniqueLibrariesByName(libraries) {
  const seen = new Set()
  return (libraries || []).filter((lib) => {
    const key = normalizedJellyfinLibraryName(lib?.name)
    if (!key || seen.has(key)) return false
    seen.add(key)
    return true
  })
}

const localFolderBlockMessage = computed(() => {
  if (localFolderBlockReason.value === 'insecure') {
    return t('settings.localFolderInsecure')
  }
  if (localFolderBlockReason.value === 'browser') {
    return t('settings.localFolderUnsupported')
  }
  return ''
})

const localDestinationHint = computed(() => {
  if (usesNativeDownloads.value) {
    return t('settings.downloadDestinationDeviceHint')
  }
  return usesBrowserDownloads.value
    ? t('settings.downloadDestinationBrowserHint')
    : t('settings.downloadDestinationLocalHint')
})

const localFolderDetailHint = computed(() => {
  if (usesNativeDownloads.value) return t('settings.deviceDownloadsHint')
  return usesBrowserDownloads.value
    ? t('settings.browserDownloadsHint')
    : t('settings.localFolderNameHint')
})

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

function logKindLabel(kind) {
  if (kind === 'artist_image') return t('metadata.artistImages')
  if (kind === 'metadata') return t('metadata.title')
  return kind
}

async function loadRepairLog() {
  repairLogLoading.value = true
  repairLogError.value = ''
  try {
    const res = await API.getRepairLog(50)
    repairLog.value = res.data || []
  } catch (err) {
    repairLogError.value =
      err?.response?.data?.detail || t('settings.logsError')
  } finally {
    repairLogLoading.value = false
  }
}

async function loadUpdateStatus(refresh = false) {
  if (!refresh && !updateStatus.value) {
    const cached = getCachedUpdateStatus()
    if (cached) updateStatus.value = cached
  }

  helpLoading.value = true
  helpError.value = ''
  try {
    updateStatus.value = await checkDowntifyVersion({ refresh })
    if (updateStatus.value?.error && !updateStatus.value?.latest_version) {
      helpError.value = updateStatus.value.error
    }
  } catch (err) {
    helpError.value =
      err?.response?.data?.detail ||
      err?.message ||
      t('settings.updateCheckError')
  } finally {
    helpLoading.value = false
  }
}

async function runNativeApkUpdate() {
  const downloadUrl = updateStatus.value?.apk_download_url
  if (!downloadUrl) {
    markUpdateFailed(t('settings.updateError'))
    return
  }

  updateWaiting.value = true
  try {
    await installApkUpdate(downloadUrl)
    updateResult.value = {
      success: true,
      mode: 'apk',
      message: t('settings.updateApkInstallerOpened'),
    }
  } catch (err) {
    markUpdateFailed(err?.message || t('settings.updateError'))
  } finally {
    updateWaiting.value = false
    updateRunning.value = false
  }
}

async function runUpdate() {
  clearUpdateTimers()
  resetUpdateFeedback()
  updateWaiting.value = false
  updateRunning.value = true
  helpError.value = ''

  if (usesApkUpdateFlow()) {
    await runNativeApkUpdate()
    return
  }

  try {
    const res = await API.updateApp()
    const data = res.data || {}
    updateResult.value = data
    if (data.current_version) updateStatus.value = data

    if (data.mode === 'noop') {
      return
    }

    if (!data.success) {
      markUpdateFailed(data.message || t('settings.updateError'))
      return
    }

    if (data.restart_scheduled) {
      updateWaiting.value = true
      waitForUpdatedApp(data.latest_version)
      return
    }

    if (data.requires_manual) {
      markUpdateFailed(data.message || t('settings.updateFailed'))
    }
  } catch (err) {
    markUpdateFailed(err?.response?.data?.detail || t('settings.updateError'))
  } finally {
    if (!updateWaiting.value) {
      updateRunning.value = false
    }
  }
}

function waitForUpdatedApp(expectedVersion, attempts = 0) {
  if (usesApkUpdateFlow()) return

  const maxAttempts = 60
  if (attempts >= maxAttempts) {
    markUpdateFailed(t('settings.updateWaitTimeout'))
    return
  }
  API.getAppVersion()
    .then((response) => {
      const version = String(response.data || '').trim()
      if (version && (!expectedVersion || version === expectedVersion)) {
        updateWaiting.value = false
        updateRunning.value = false
        updateCompleted.value = true
        updateStatus.value = {
          ...(updateStatus.value || {}),
          current_version: version,
          latest_version: version,
          connected_server_version: version,
          version_mismatch: false,
          update_available: false,
          needs_apk_update: false,
          needs_server_update: false,
        }
        return
      }
      updateCompletionTimer = setTimeout(
        () => waitForUpdatedApp(expectedVersion, attempts + 1),
        1500
      )
    })
    .catch(() => {
      updateCompletionTimer = setTimeout(
        () => waitForUpdatedApp(expectedVersion, attempts + 1),
        1500
      )
    })
}

function refreshPage() {
  window.location.reload()
}

async function selectLocalDestination() {
  if (isLocal.value && localFolderName.value) return

  folderPickerError.value = ''
  try {
    await activateLocalDestination()
  } catch (err) {
    if (err?.name === 'AbortError') return
    if (
      ['insecure', 'browser', 'unsupported', 'unavailable'].includes(
        err?.message
      )
    ) {
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
    if (
      ['insecure', 'browser', 'unsupported', 'unavailable'].includes(
        err?.message
      )
    ) {
      folderPickerError.value = localFolderErrorMessage(err.message)
      return
    }
    folderPickerError.value = err?.message || t('settings.localFolderError')
  }
}

async function onJellyfinConfigChange() {
  const url = sm.settings.value.jellyfin_url?.trim()
  const apiKey = sm.settings.value.jellyfin_api_key?.trim()

  console.log('Jellyfin config changed:', {
    url: url ? '***' : '',
    hasApiKey: !!apiKey,
  })

  jellyfinLibraryError.value = ''
  jellyfinLibraries.value = []

  if (!url || !apiKey) {
    console.log('Missing Jellyfin URL or API key')
    return
  }

  jellyfinLibraryLoading.value = true
  try {
    console.log('Fetching Jellyfin libraries from:', url)
    const response = await API.getJellyfinLibraries(url, apiKey)
    console.log('Jellyfin libraries response:', response)

    if (response.status === 200 && response.data.success) {
      jellyfinLibraries.value = uniqueLibrariesByName(response.data.libraries)
      console.log('Successfully loaded libraries:', jellyfinLibraries.value)
      console.log('Libraries count:', jellyfinLibraries.value.length)
      console.log(
        'Library names:',
        jellyfinLibraries.value.map((lib) => `${lib.name} (id: ${lib.id})`)
      )
      console.log(
        'Library normalized keys:',
        jellyfinLibraries.value.map((lib) =>
          normalizedJellyfinLibraryName(lib.name)
        )
      )
      console.log(
        'Displayed library names:',
        uniqueJellyfinLibraries.value.map(
          (lib) => `${lib.name} (id: ${lib.id})`
        )
      )

      if (jellyfinLibraries.value.length === 0) {
        jellyfinLibraryError.value = t('settings.jellyfinNoLibraries')
      }
    } else {
      jellyfinLibraryError.value =
        t('settings.jellyfinLibraryError') + ': Invalid response'
    }
  } catch (err) {
    console.error('Failed to fetch Jellyfin libraries:', err)
    const errorDetail =
      err.response?.data?.detail || err.message || 'Unknown error'
    jellyfinLibraryError.value = `${t(
      'settings.jellyfinLibraryError'
    )}: ${errorDetail}`
  } finally {
    jellyfinLibraryLoading.value = false
  }
}

async function testServerConnection() {
  serverTestMessage.value = ''
  serverTestError.value = false
  const parsed = parseServerUrl(serverUrlInput.value)
  if (!parsed) {
    serverTestError.value = true
    serverTestMessage.value = t('settings.serverInvalidUrl')
    return
  }
  serverTestLoading.value = true
  try {
    const client = axios.create({
      baseURL: buildApiBaseUrl(parsed),
      timeout: 15000,
    })
    const [healthRes, versionRes] = await Promise.all([
      client.get('/api/health'),
      client.get('/api/version'),
    ])
    const version = String(versionRes.data || '').trim()
    if (!healthRes.data || healthRes.status !== 200) {
      throw new Error(t('settings.serverTestFailed'))
    }
    serverTestMessage.value = t('settings.serverTestSuccess', {
      version: version || '?',
    })
  } catch (err) {
    serverTestError.value = true
    const detail = err?.response?.data?.detail || err?.message
    serverTestMessage.value = detail
      ? `${t('settings.serverTestFailed')}: ${detail}`
      : t('settings.serverTestFailed')
  } finally {
    serverTestLoading.value = false
  }
}

function reloadAfterServerChange() {
  if (isCapacitorNative()) {
    API.reconnectBackend()
    window.location.reload()
    return
  }
  window.location.reload()
}

function connectToThisDevice() {
  const current = getCurrentPageServerUrl()
  if (!current) return
  serverUrlInput.value = current
  if (isConnectedToCurrentPage()) return
  setStoredServerUrl(current)
  reloadAfterServerChange()
}

function saveServerConnection() {
  const parsed = parseServerUrl(serverUrlInput.value)
  if (!parsed) {
    serverTestError.value = true
    serverTestMessage.value = t('settings.serverInvalidUrl')
    return
  }
  setStoredServerUrl(serverUrlInput.value.trim())
  reloadAfterServerChange()
}

function resetServerConnection() {
  setStoredServerUrl('')
  reloadAfterServerChange()
}

function selectConnectionMode(mode) {
  const normalized = mode === 'server' ? 'server' : 'device'
  if (connectionMode.value === normalized) return
  connectionMode.value = normalized
  setConnectionMode(normalized)
  reloadAfterServerChange()
}

async function testJellyfinApi() {
  const url = sm.settings.value.jellyfin_url?.trim()
  const apiKey = sm.settings.value.jellyfin_api_key?.trim()
  if (!url || !apiKey) return

  jellyfinTestLoading.value = true
  jellyfinTestMessage.value = ''
  jellyfinTestError.value = false
  try {
    const response = await API.getJellyfinLibraries(url, apiKey)
    if (response.status !== 200 || !response.data.success) {
      throw new Error(t('settings.jellyfinTestFailed'))
    }
    jellyfinLibraries.value = uniqueLibrariesByName(response.data.libraries)
    jellyfinLibraryError.value = jellyfinLibraries.value.length
      ? ''
      : t('settings.jellyfinNoLibraries')
    jellyfinTestMessage.value = t('settings.jellyfinTestSuccess')
  } catch (err) {
    jellyfinTestError.value = true
    const detail = err.response?.data?.detail || err.message
    jellyfinTestMessage.value = detail
      ? `${t('settings.jellyfinTestFailed')}: ${detail}`
      : t('settings.jellyfinTestFailed')
  } finally {
    jellyfinTestLoading.value = false
  }
}

watch(activeTab, (newTab) => {
  if (newTab === 'api') {
    const hasUrl = sm.settings.value.jellyfin_url?.trim()
    const hasApiKey = sm.settings.value.jellyfin_api_key?.trim()
    if (
      hasUrl &&
      hasApiKey &&
      jellyfinLibraries.value.length === 0 &&
      !jellyfinLibraryError.value
    ) {
      onJellyfinConfigChange()
    }
  }
  if (newTab === 'logs') {
    loadRepairLog()
  }
  if (newTab === 'help') {
    loadUpdateStatus()
  }
})

watch(
  () => route.query.tab,
  (tab) => {
    if (typeof tab === 'string') applySettingsTab(tab)
  },
  { immediate: true }
)
</script>
