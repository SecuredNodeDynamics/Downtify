<template>
  <div class="player-view min-h-0 overflow-x-hidden">
    <Navbar />

    <div
      class="player-page mx-auto flex w-full max-w-5xl min-h-0 flex-1 flex-col px-4 py-2 sm:px-6 sm:py-8"
    >
      <!-- Header -->
      <div class="mb-4 sm:mb-8 mobile-page-header shrink-0">
        <h1 class="text-2xl font-bold tracking-tight">
          {{ t('player.title') }}
        </h1>
        <p class="mt-1 text-sm text-base-content/60">
          {{ t('player.subtitle') }}
        </p>
      </div>

      <!-- Empty state -->
      <div
        v-if="files.length === 0 && !loading"
        class="surface rounded-2xl p-12 flex flex-col items-center text-center"
      >
        <Icon
          icon="clarity:headphones-line"
          class="h-12 w-12 text-base-content/20 mb-4"
        />
        <p class="text-base-content/50 text-sm">{{ t('player.empty') }}</p>
        <p class="text-base-content/40 text-xs mt-1">
          {{ t('player.emptyHint') }}
        </p>
      </div>

      <!-- Skeleton -->
      <div
        v-else-if="loading && files.length === 0 && libraryItems.length === 0"
        class="space-y-3"
      >
        <div class="skeleton h-52 rounded-3xl lg:h-72" />
        <div class="skeleton h-16 rounded-2xl" />
        <div class="skeleton h-16 rounded-2xl" />
      </div>

      <!-- Player + queue -->
      <div v-else class="player-content min-h-0 flex-1">
        <div class="player-shell min-h-0">
          <!-- Now playing -->
          <section class="panel-glow-shell surface shrink-0 grow-0 rounded-3xl">
            <div
              class="player-now flex flex-col items-center rounded-3xl p-3 text-center sm:p-8"
            >
              <!-- Cover -->
              <div
                class="player-cover relative flex items-center justify-center overflow-hidden rounded-2xl text-primary sm:rounded-3xl"
                :class="{
                  'player-cover-active': hasActiveTrack,
                  'opacity-80': !hasActiveTrack,
                }"
              >
                <div class="player-cover-frame">
                  <CoverImage
                    v-if="
                      hasActiveTrack &&
                      (currentCoverSources.src ||
                        currentCoverSources.fallbacks.length)
                    "
                    :key="player.currentTrack.value?.file || 'player-cover'"
                    :src="currentCoverSources.src"
                    :fallbacks="currentCoverSources.fallbacks"
                    :alt="trackTitle"
                    img-class="absolute inset-0 h-full w-full object-cover"
                    eager
                  >
                    <template #fallback>
                      <Icon
                        icon="clarity:music-note-line"
                        class="h-16 w-16 sm:h-24 sm:w-24"
                      />
                    </template>
                  </CoverImage>
                  <Icon
                    v-else
                    icon="clarity:music-note-line"
                    class="h-16 w-16 sm:h-24 sm:w-24"
                  />
                </div>
                <div
                  v-if="player.isPlaying.value"
                  class="absolute bottom-2 right-2 equalizer h-5 sm:bottom-3 sm:right-3"
                  aria-hidden="true"
                >
                  <span></span><span></span><span></span>
                </div>
              </div>

              <!-- Title / artist -->
              <div class="mt-3 min-w-0 max-w-full w-full sm:mt-6">
                <p class="text-lg font-bold tracking-tight truncate sm:text-xl">
                  {{ trackTitle }}
                </p>
                <p class="mt-0.5 text-sm text-base-content/60 truncate">
                  <span v-if="trackArtist">{{ trackArtist }}</span>
                  <span
                    v-else-if="!hasActiveTrack"
                    class="text-base-content/40"
                  >
                    {{ t('player.nothingPlayingHint') }}
                  </span>
                </p>
                <div v-if="playerContextLabel" class="mt-2 flex justify-center">
                  <span
                    class="inline-flex max-w-full items-center gap-1.5 rounded-full border border-primary/25 bg-primary/10 px-3 py-1 text-xs font-medium text-primary"
                  >
                    <Icon
                      :icon="playerContextIcon"
                      class="h-3.5 w-3.5 shrink-0"
                    />
                    <span class="truncate">{{ playerContextLabel }}</span>
                  </span>
                </div>
              </div>

              <!-- Progress -->
              <div class="mt-3 w-full sm:mt-6">
                <div
                  class="player-progress"
                  :class="{
                    'player-progress--scrubbing': isScrubbing,
                    'pointer-events-none opacity-50': !hasActiveTrack,
                  }"
                  ref="progressBar"
                  role="slider"
                  tabindex="0"
                  :aria-label="t('player.seek')"
                  :aria-valuemin="0"
                  :aria-valuemax="Math.floor(player.duration.value || 0)"
                  :aria-valuenow="Math.floor(player.currentTime.value || 0)"
                  :aria-valuetext="`${formatTime(
                    player.currentTime.value
                  )} / ${formatTime(player.duration.value)}`"
                  @pointerdown="onSeekStart"
                  @keydown="onSeekKeydown"
                >
                  <div class="player-progress-track" ref="progressTrack">
                    <div
                      class="player-progress-fill"
                      :style="{ width: `${displayProgressPct}%` }"
                    />
                    <div
                      class="player-progress-thumb"
                      :style="{ left: `${displayProgressPct}%` }"
                    />
                  </div>
                </div>
                <div
                  class="mt-1 flex items-center justify-between text-xs text-base-content/50 tabular-nums sm:mt-2"
                >
                  <span>{{ formatTime(player.currentTime.value) }}</span>
                  <span>{{ formatTime(player.duration.value) }}</span>
                </div>
              </div>

              <!-- Transport -->
              <div
                class="mt-3 flex items-center justify-center gap-2 sm:mt-5 sm:gap-3"
              >
                <button
                  class="icon-btn h-9 w-9 sm:h-10 sm:w-10"
                  :class="{ 'icon-btn-active': player.shuffle.value }"
                  @click="player.toggleShuffle()"
                  :title="
                    player.shuffle.value
                      ? t('player.shuffleOn')
                      : t('player.shuffleOff')
                  "
                >
                  <Icon
                    icon="clarity:shuffle-line"
                    class="h-4 w-4 sm:h-5 sm:w-5"
                  />
                </button>
                <button
                  class="icon-btn h-10 w-10 sm:h-10 sm:w-10"
                  @click="player.prev()"
                  :title="t('player.previous')"
                  :disabled="!hasActiveTrack"
                >
                  <Icon
                    icon="clarity:step-forward-2-line"
                    class="h-5 w-5 -scale-x-100"
                  />
                </button>
                <button
                  class="player-play-btn inline-flex items-center justify-center rounded-full shadow-glow-sm transition hover:scale-105 active:scale-95 disabled:opacity-50"
                  :class="
                    player.isPlaying.value
                      ? 'bg-amber-300 text-amber-950 hover:bg-amber-200'
                      : 'bg-primary text-primary-content'
                  "
                  @click="player.toggle()"
                  :disabled="files.length === 0"
                  :title="
                    player.isPlaying.value
                      ? t('player.pause')
                      : t('player.play')
                  "
                >
                  <Icon
                    :icon="
                      player.isPlaying.value
                        ? 'clarity:pause-solid'
                        : 'clarity:play-solid'
                    "
                    class="h-7 w-7 sm:h-6 sm:w-6"
                  />
                </button>
                <button
                  class="icon-btn h-10 w-10 sm:h-10 sm:w-10"
                  @click="player.next()"
                  :title="t('player.next')"
                  :disabled="!hasActiveTrack"
                >
                  <Icon icon="clarity:step-forward-2-line" class="h-5 w-5" />
                </button>
                <button
                  class="icon-btn relative h-9 w-9 sm:h-10 sm:w-10"
                  :class="{
                    'icon-btn-active': player.repeatMode.value !== 'off',
                  }"
                  @click="player.cycleRepeat()"
                  :title="repeatTitle"
                >
                  <Icon
                    icon="clarity:refresh-line"
                    class="h-4 w-4 sm:h-5 sm:w-5"
                  />
                  <span
                    v-if="player.repeatMode.value === 'one'"
                    class="absolute -bottom-0.5 -right-0.5 flex h-4 min-w-[1rem] items-center justify-center rounded-full bg-primary px-1 text-[9px] font-bold text-primary-content"
                  >
                    1
                  </span>
                </button>
                <button
                  v-if="lyricsAvailable"
                  class="icon-btn h-9 w-9 sm:h-10 sm:w-10"
                  :class="{ 'icon-btn-active': lyricsOpen }"
                  @click="lyricsOpen = !lyricsOpen"
                  :title="t('player.lyrics')"
                >
                  <Icon
                    icon="clarity:music-note-line"
                    class="h-4 w-4 sm:h-5 sm:w-5"
                  />
                </button>
              </div>

              <section
                v-if="lyricsAvailable && lyricsOpen"
                class="lyrics-preview mt-4 w-full rounded-2xl border border-white/10 bg-base-100/55 p-3 text-left sm:mt-5 sm:p-4"
              >
                <div class="mb-2 flex items-center justify-between gap-3">
                  <h2
                    class="text-xs font-semibold uppercase tracking-wider text-base-content/45"
                  >
                    {{ t('player.lyrics') }}
                  </h2>
                  <div class="flex items-center gap-1.5">
                    <span class="text-xs tabular-nums text-base-content/40">
                      {{ formatTime(player.currentTime.value) }}
                    </span>
                    <div
                      v-if="syncedLyrics.length"
                      class="lyrics-offset-controls"
                      :aria-label="t('player.lyricsOffset')"
                    >
                      <button
                        type="button"
                        class="lyrics-offset-btn"
                        :title="t('player.lyricsEarlier')"
                        @click="adjustLyricsOffset(-0.1)"
                      >
                        <Icon icon="clarity:minus-line" class="h-3.5 w-3.5" />
                      </button>
                      <button
                        type="button"
                        class="lyrics-offset-value"
                        :title="t('player.lyricsReset')"
                        @click="resetLyricsOffset"
                      >
                        {{ lyricsOffsetLabel }}
                      </button>
                      <button
                        type="button"
                        class="lyrics-offset-btn"
                        :title="t('player.lyricsLater')"
                        @click="adjustLyricsOffset(0.1)"
                      >
                        <Icon icon="clarity:plus-line" class="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                </div>
                <div
                  v-if="syncedLyrics.length"
                  ref="lyricsScroller"
                  class="lyrics-scroll"
                >
                  <p
                    v-for="(line, index) in syncedLyrics"
                    :key="`${line.time}:${index}`"
                    :ref="(el) => setLyricLineRef(el, index)"
                    class="lyrics-line"
                    :class="{
                      'lyrics-line-active': index === activeLyricIndex,
                    }"
                  >
                    {{ line.text }}
                  </p>
                </div>
                <p v-else class="lyrics-plain">
                  {{ lyricsPlain }}
                </p>
              </section>

              <!-- Volume (desktop only — mobile uses device volume) -->
              <div
                class="mt-6 hidden w-full max-w-xs items-center gap-3 lg:flex"
              >
                <button
                  class="icon-btn"
                  @click="player.toggleMute()"
                  :title="
                    player.isMuted.value ? t('player.unmute') : t('player.mute')
                  "
                >
                  <Icon
                    :icon="
                      player.isMuted.value || player.volume.value === 0
                        ? 'clarity:volume-mute-line'
                        : player.volume.value < 0.5
                          ? 'clarity:volume-down-line'
                          : 'clarity:volume-up-line'
                    "
                    class="h-5 w-5"
                  />
                </button>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.01"
                  :value="player.isMuted.value ? 0 : player.volume.value"
                  @input="onVolume($event)"
                  class="player-range flex-1"
                  :title="t('player.volume')"
                />
              </div>

              <section
                v-if="queueDisplayTracks.length"
                class="player-queue mt-5 w-full text-left"
              >
                <div class="mb-2 flex items-center justify-between gap-3">
                  <h2 class="player-detail-heading">
                    {{ t('player.upNext') }}
                  </h2>
                  <span class="text-xs text-base-content/45">
                    {{
                      t('player.countMany', {
                        count: queueDisplayTracks.length,
                      })
                    }}
                  </span>
                </div>
                <div class="player-queue-list">
                  <button
                    v-for="item in visibleQueueTracks"
                    :key="item.track.file"
                    type="button"
                    class="player-queue-item"
                    :title="item.track.title"
                    @click="openQueueTrack(item)"
                  >
                    <div class="player-queue-cover">
                      <CoverImage
                        :src="coverSourcesFor(item.track.file).src"
                        :fallbacks="coverSourcesFor(item.track.file).fallbacks"
                        :alt="item.track.title"
                        img-class="absolute inset-0 h-full w-full object-cover"
                        eager
                      >
                        <template #fallback>
                          <Icon
                            icon="clarity:music-note-line"
                            class="h-5 w-5 text-base-content/40"
                          />
                        </template>
                      </CoverImage>
                    </div>
                    <div class="min-w-0 flex-1">
                      <p class="truncate text-sm font-semibold">
                        {{ item.track.title }}
                      </p>
                      <p class="truncate text-xs text-base-content/45">
                        {{ queueTrackArtist(item.track) }}
                      </p>
                    </div>
                    <Icon
                      icon="clarity:info-standard-line"
                      class="h-4 w-4 shrink-0 text-base-content/35"
                    />
                  </button>
                </div>
              </section>
              <section
                v-else-if="hasActiveTrack"
                class="player-queue mt-5 w-full text-left"
              >
                <div class="mb-2 flex items-center justify-between gap-3">
                  <h2 class="player-detail-heading">
                    {{ t('player.upNext') }}
                  </h2>
                </div>
                <p class="text-sm text-base-content/45">
                  {{ t('player.queueEmpty') }}
                </p>
              </section>
            </div>
          </section>

          <!-- Artist & album details -->
          <aside
            class="panel-glow-shell panel-glow-shell-grow surface min-h-0 rounded-3xl"
          >
            <div
              class="player-details flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto p-3 sm:gap-5 sm:p-5"
            >
              <template
                v-if="
                  hasActiveTrack &&
                  (currentArtistEntry || currentArtistAlbums.length)
                "
              >
                <section v-if="currentArtistEntry" class="space-y-2">
                  <h2 class="player-detail-heading">
                    {{ t('library.artists') }}
                  </h2>
                  <article class="player-detail-card">
                    <div class="player-detail-main">
                      <div class="player-detail-cover">
                        <CoverImage
                          v-if="
                            artistCoverFor(currentArtistEntry).src ||
                            artistCoverFor(currentArtistEntry).fallbacks.length
                          "
                          :key="`player-artist:${currentArtistEntry.name}`"
                          :src="artistCoverFor(currentArtistEntry).src"
                          :fallbacks="
                            artistCoverFor(currentArtistEntry).fallbacks
                          "
                          :alt="currentArtistEntry.name"
                          img-class="absolute inset-0 h-full w-full object-cover"
                          eager
                        >
                          <template #fallback>
                            <Icon
                              icon="clarity:user-line"
                              class="absolute left-1/2 top-1/2 h-7 w-7 -translate-x-1/2 -translate-y-1/2 text-base-content/40"
                            />
                          </template>
                        </CoverImage>
                        <Icon
                          v-else
                          icon="clarity:user-line"
                          class="absolute left-1/2 top-1/2 h-7 w-7 -translate-x-1/2 -translate-y-1/2 text-base-content/40"
                        />
                      </div>
                      <div class="min-w-0 flex-1">
                        <p class="player-detail-title">
                          {{ currentArtistEntry.name }}
                        </p>
                        <p class="player-detail-meta">
                          {{
                            t('library.artistMeta', {
                              tracks: currentArtistEntry.files.length,
                              albums: currentArtistEntry.albumCount,
                            })
                          }}
                        </p>
                      </div>
                    </div>
                    <div class="player-detail-actions player-artist-actions">
                      <button
                        type="button"
                        class="btn btn-primary btn-sm inline-flex h-9 shrink-0 items-center gap-1.5 whitespace-nowrap rounded-full px-3 sm:px-4"
                        @click="
                          playFiles(currentArtistEntry.files, null, {
                            type: 'artist',
                            name: currentArtistEntry.name,
                          })
                        "
                      >
                        <Icon
                          icon="clarity:play-line"
                          class="h-4 w-4 shrink-0"
                        />
                        {{ t('library.playArtist') }}
                      </button>
                      <LibraryArtistMonitor
                        :artist-name="currentArtistEntry.name"
                      />
                    </div>
                  </article>
                </section>

                <section v-if="currentArtistAlbums.length" class="space-y-2">
                  <h2 class="player-detail-heading">
                    {{ t('library.albums') }}
                  </h2>
                  <article
                    v-for="album in currentArtistAlbums"
                    :key="album.key"
                    class="player-detail-card"
                    :class="{
                      'player-detail-card-active':
                        album.key === currentAlbumKey,
                    }"
                  >
                    <div class="player-detail-main">
                      <div class="player-detail-cover">
                        <CoverImage
                          :key="album.coverFile"
                          :src="coverSourcesFor(album.coverFile).src"
                          :fallbacks="
                            coverSourcesFor(album.coverFile).fallbacks
                          "
                          :alt="album.name"
                          img-class="absolute inset-0 h-full w-full object-cover"
                          eager
                        >
                          <template #fallback>
                            <Icon
                              icon="clarity:album-line"
                              class="absolute left-1/2 top-1/2 h-7 w-7 -translate-x-1/2 -translate-y-1/2 text-base-content/40"
                            />
                          </template>
                        </CoverImage>
                      </div>
                      <div class="min-w-0 flex-1">
                        <p class="player-detail-title">{{ album.name }}</p>
                        <p class="player-detail-meta">
                          {{
                            t('library.albumMeta', {
                              tracks: album.files.length,
                            })
                          }}
                        </p>
                      </div>
                    </div>
                    <div class="player-detail-actions">
                      <button
                        type="button"
                        class="btn btn-primary btn-sm inline-flex h-9 shrink-0 items-center gap-1.5 whitespace-nowrap rounded-full px-3 sm:px-4"
                        @click="
                          playFiles(album.files, null, {
                            type: 'album',
                            name: album.name,
                            artist: album.artist,
                          })
                        "
                      >
                        <Icon
                          icon="clarity:play-line"
                          class="h-4 w-4 shrink-0"
                        />
                        {{ t('library.playAlbum') }}
                      </button>
                    </div>
                  </article>
                </section>
              </template>

              <div
                v-else
                class="flex flex-1 items-center justify-center py-10 text-center"
              >
                <p class="text-sm text-base-content/50">
                  {{ t('player.detailsEmpty') }}
                </p>
              </div>
            </div>
          </aside>
        </div>

        <section
          v-if="currentArtistName"
          class="similar-artists-card panel-glow-shell surface"
        >
          <div class="p-3 sm:p-4">
            <div class="flex items-center justify-between gap-3">
              <h2 class="player-detail-heading">
                {{ t('player.similarMedia') }}
              </h2>
              <div class="tabs tabs-boxed bg-base-100/60 p-0.5">
                <button
                  type="button"
                  class="tab h-7 min-h-0 px-3 text-xs"
                  :class="{ 'tab-active': similarMediaTab === 'artists' }"
                  @click="similarMediaTab = 'artists'"
                >
                  {{ t('library.artists') }}
                </button>
                <button
                  type="button"
                  class="tab h-7 min-h-0 px-3 text-xs"
                  :class="{ 'tab-active': similarMediaTab === 'tracks' }"
                  @click="similarMediaTab = 'tracks'"
                >
                  {{ t('library.tracks') }}
                </button>
              </div>
            </div>
            <div
              v-if="
                similarMediaTab === 'artists'
                  ? similarArtistsLoading
                  : similarTracksLoading
              "
              class="similar-artists-grid mt-2.5"
              aria-hidden="true"
              @pointerdown="startSimilarMediaDrag"
              @pointermove="moveSimilarMediaDrag"
              @pointerup="endSimilarMediaDrag"
              @pointercancel="endSimilarMediaDrag"
              @click.capture="suppressSimilarMediaClick"
            >
              <div v-for="index in 16" :key="index" class="similar-artist-item">
                <div class="skeleton similar-artist-cover" />
                <div class="skeleton mx-auto mt-1.5 h-3 w-14 rounded" />
              </div>
            </div>
            <div
              v-else-if="similarMediaTab === 'artists' && similarArtists.length"
              class="similar-artists-grid mt-2.5"
              @pointerdown="startSimilarMediaDrag"
              @pointermove="moveSimilarMediaDrag"
              @pointerup="endSimilarMediaDrag"
              @pointercancel="endSimilarMediaDrag"
              @click.capture="suppressSimilarMediaClick"
            >
              <button
                v-for="artist in similarArtists"
                :key="artist.browse_id || artist.name"
                type="button"
                class="similar-artist-item"
                @click="openSimilarArtist(artist)"
              >
                <div class="similar-artist-cover">
                  <CoverImage
                    v-if="similarArtistCoverSources(artist).src"
                    :src="similarArtistCoverSources(artist).src"
                    :fallbacks="similarArtistCoverSources(artist).fallbacks"
                    :alt="artist.name"
                    img-class="absolute inset-0 h-full w-full object-cover"
                    eager
                  >
                    <template #fallback>
                      <Icon
                        icon="clarity:user-line"
                        class="absolute left-1/2 top-1/2 h-6 w-6 -translate-x-1/2 -translate-y-1/2 text-base-content/40"
                      />
                    </template>
                  </CoverImage>
                  <Icon
                    v-else
                    icon="clarity:user-line"
                    class="absolute left-1/2 top-1/2 h-6 w-6 -translate-x-1/2 -translate-y-1/2 text-base-content/40"
                  />
                  <span
                    v-if="isSimilarArtistOwned(artist)"
                    class="similar-owned-badge"
                    :title="t('search.inLibrary')"
                  >
                    <Icon icon="clarity:library-solid" class="h-3.5 w-3.5" />
                  </span>
                </div>
                <p class="similar-artist-name" :title="artist.name">
                  {{ artist.name }}
                </p>
              </button>
            </div>
            <div
              v-else-if="similarMediaTab === 'tracks' && similarTracks.length"
              class="similar-artists-grid mt-2.5"
              @pointerdown="startSimilarMediaDrag"
              @pointermove="moveSimilarMediaDrag"
              @pointerup="endSimilarMediaDrag"
              @pointercancel="endSimilarMediaDrag"
              @click.capture="suppressSimilarMediaClick"
            >
              <article
                v-for="track in similarTracks"
                :key="track.song_id || track.url"
                class="similar-track-item"
                role="button"
                tabindex="0"
                @click="openSimilarTrack(track)"
                @keydown.enter.prevent="openSimilarTrack(track)"
                @keydown.space.prevent="openSimilarTrack(track)"
              >
                <div class="similar-artist-cover">
                  <CoverImage
                    v-if="track.cover_url"
                    :src="API.remoteCoverSources(track.cover_url, 192).src"
                    :fallbacks="
                      API.remoteCoverSources(track.cover_url, 192).fallbacks
                    "
                    :alt="track.name"
                    img-class="absolute inset-0 h-full w-full object-cover"
                    eager
                  >
                    <template #fallback>
                      <Icon
                        icon="clarity:music-note-line"
                        class="h-6 w-6 text-base-content/40"
                      />
                    </template>
                  </CoverImage>
                </div>
                <div class="mt-1.5 flex min-w-0 items-start gap-1">
                  <div class="min-w-0 flex-1">
                    <p class="similar-artist-name mt-0" :title="track.name">
                      {{ track.name }}
                    </p>
                    <p class="truncate text-[10px] text-base-content/45">
                      {{ resultArtistLabel(track) }}
                    </p>
                  </div>
                  <button
                    v-if="!similarTrackOwnership.isOwned(track)"
                    type="button"
                    class="similar-track-download"
                    :class="downloadButtonClass(track)"
                    :title="t('common.download')"
                    @click.stop="downloadSimilarArtistItem(track)"
                  >
                    <Icon
                      :icon="downloadButtonIcon(track)"
                      class="h-3.5 w-3.5"
                    />
                  </button>
                  <span
                    v-else
                    class="similar-track-owned"
                    :title="t('search.inLibrary')"
                  >
                    <Icon icon="clarity:library-solid" class="h-3.5 w-3.5" />
                  </span>
                </div>
              </article>
            </div>
            <p v-else class="player-detail-empty mt-3">
              {{
                similarMediaTab === 'artists'
                  ? t('player.similarArtistsEmpty')
                  : t('player.similarTracksEmpty')
              }}
            </p>
          </div>
        </section>
      </div>
    </div>

    <Teleport to="body">
      <div
        v-if="selectedSimilarArtist"
        class="artist-modal-backdrop"
        @click.self="closeSimilarArtist"
      >
        <section
          class="artist-modal surface-strong"
          role="dialog"
          aria-modal="true"
          :aria-label="selectedSimilarArtist.name"
        >
          <header class="artist-modal-header">
            <div class="flex min-w-0 items-center gap-3">
              <div class="artist-modal-avatar">
                <CoverImage
                  v-if="similarArtistCoverSources(selectedSimilarArtist).src"
                  :src="similarArtistCoverSources(selectedSimilarArtist).src"
                  :fallbacks="
                    similarArtistCoverSources(selectedSimilarArtist).fallbacks
                  "
                  :alt="selectedSimilarArtist.name"
                  img-class="absolute inset-0 h-full w-full object-cover"
                />
                <Icon
                  v-else
                  icon="clarity:user-line"
                  class="h-7 w-7 text-base-content/40"
                />
              </div>
              <div class="min-w-0">
                <h2 class="truncate text-lg font-bold">
                  {{ selectedSimilarArtist.name }}
                </h2>
                <p class="text-xs text-base-content/50">
                  {{ t('player.artistAvailableMusic') }}
                </p>
              </div>
            </div>
            <button
              type="button"
              class="icon-btn shrink-0"
              :title="t('common.close')"
              @click="closeSimilarArtist"
            >
              <Icon icon="clarity:close-line" class="h-5 w-5" />
            </button>
          </header>

          <div class="artist-modal-toolbar">
            <div class="tabs tabs-boxed bg-base-100/60 p-1">
              <button
                type="button"
                class="tab"
                :class="{ 'tab-active': similarArtistTab === 'albums' }"
                @click="similarArtistTab = 'albums'"
              >
                {{ t('library.albums') }} ({{ similarArtistAlbums.length }})
              </button>
              <button
                type="button"
                class="tab"
                :class="{ 'tab-active': similarArtistTab === 'tracks' }"
                @click="similarArtistTab = 'tracks'"
              >
                {{ t('library.tracks') }} ({{ similarArtistTracks.length }})
              </button>
            </div>
            <LibraryArtistMonitor :artist-name="selectedSimilarArtist.name" />
          </div>

          <div class="artist-modal-results">
            <div v-if="similarArtistDetailsLoading" class="space-y-2">
              <div
                v-for="index in 5"
                :key="index"
                class="skeleton h-16 rounded-lg"
              />
            </div>
            <div
              v-else-if="visibleSimilarArtistResults.length"
              class="space-y-2"
            >
              <article
                v-for="item in visibleSimilarArtistResults"
                :key="item.song_id || item.url"
                class="artist-result"
              >
                <div class="artist-result-cover">
                  <CoverImage
                    v-if="item.cover_url"
                    :src="API.remoteCoverSources(item.cover_url, 160).src"
                    :fallbacks="
                      API.remoteCoverSources(item.cover_url, 160).fallbacks
                    "
                    :alt="item.name"
                    img-class="absolute inset-0 h-full w-full object-cover"
                    eager
                  />
                </div>
                <div class="min-w-0 flex-1">
                  <p class="truncate text-sm font-semibold">{{ item.name }}</p>
                  <p class="truncate text-xs text-base-content/50">
                    {{ resultArtistLabel(item) }}
                  </p>
                  <p
                    v-if="
                      similarArtistTab === 'albums' &&
                      similarArtistAlbumTrackCountLabel(item)
                    "
                    class="truncate text-xs text-base-content/40"
                  >
                    {{ similarArtistAlbumTrackCountLabel(item) }}
                  </p>
                </div>
                <button
                  v-if="!similarTrackOwnership.isOwned(selectedSimilarTrack)"
                  type="button"
                  class="icon-btn shrink-0 text-primary"
                  :class="downloadButtonClass(item)"
                  :title="t('common.download')"
                  @click="downloadSimilarArtistItem(item)"
                >
                  <Icon :icon="downloadButtonIcon(item)" class="h-5 w-5" />
                </button>
              </article>
            </div>
            <p v-else class="py-12 text-center text-sm text-base-content/50">
              {{ t('player.artistMusicEmpty') }}
            </p>
          </div>
        </section>
      </div>
    </Teleport>

    <Teleport to="body">
      <div
        v-if="selectedQueueTrack"
        class="artist-modal-backdrop"
        @click.self="closeQueueTrack"
      >
        <section
          class="track-modal surface-strong"
          role="dialog"
          aria-modal="true"
          :aria-label="selectedQueueTrack.track.title"
        >
          <header class="artist-modal-header">
            <div class="min-w-0 flex-1">
              <h2 class="truncate text-lg font-bold">
                {{ selectedQueueTrack.track.title }}
              </h2>
              <p class="truncate text-xs text-base-content/50">
                {{ queueTrackArtist(selectedQueueTrack.track) }}
              </p>
            </div>
            <div class="flex shrink-0 items-center gap-2">
              <button
                type="button"
                class="btn btn-primary btn-sm h-10 rounded-full px-4"
                @click="player.playAt(selectedQueueTrack.index)"
              >
                <Icon icon="clarity:play-line" class="h-4 w-4" />
                {{ t('player.play') }}
              </button>
              <button
                type="button"
                class="icon-btn shrink-0"
                :title="t('common.close')"
                @click="closeQueueTrack"
              >
                <Icon icon="clarity:close-line" class="h-5 w-5" />
              </button>
            </div>
          </header>

          <div class="track-modal-body">
            <div class="track-modal-summary">
              <div class="track-modal-cover">
                <CoverImage
                  :src="coverSourcesFor(selectedQueueTrack.track.file).src"
                  :fallbacks="
                    coverSourcesFor(selectedQueueTrack.track.file).fallbacks
                  "
                  :alt="selectedQueueTrack.track.title"
                  img-class="absolute inset-0 h-full w-full object-cover"
                >
                  <template #fallback>
                    <Icon
                      icon="clarity:music-note-line"
                      class="h-12 w-12 text-base-content/35"
                    />
                  </template>
                </CoverImage>
              </div>

              <div class="min-w-0 flex-1">
                <dl class="track-modal-metadata mt-0">
                  <div>
                    <dt>{{ t('library.artists') }}</dt>
                    <dd>{{ queueTrackArtist(selectedQueueTrack.track) }}</dd>
                  </div>
                  <div v-if="selectedQueueTrackLibraryItem?.album">
                    <dt>{{ t('library.albums') }}</dt>
                    <dd>{{ selectedQueueTrackLibraryItem.album }}</dd>
                  </div>
                  <div>
                    <dt>{{ t('player.queuePosition') }}</dt>
                    <dd>{{ selectedQueueTrack.offset }}</dd>
                  </div>
                </dl>
              </div>
            </div>

            <div v-if="selectedQueueAlbum" class="track-modal-current-album">
              <div class="min-w-0">
                <p class="truncate text-sm font-semibold">
                  {{ selectedQueueAlbum.name }}
                </p>
                <p class="text-xs text-base-content/50">
                  {{
                    selectedQueueAlbumExpectedCount
                      ? t('player.albumCompleteness', {
                          have: selectedQueueAlbum.files.length,
                          total: selectedQueueAlbumExpectedCount,
                        })
                      : t('library.albumMeta', {
                          tracks: selectedQueueAlbum.files.length,
                        })
                  }}
                </p>
              </div>
              <span
                class="inline-flex shrink-0 items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold"
                :class="
                  selectedQueueAlbumMissingCount > 0
                    ? 'bg-amber-300/15 text-amber-200'
                    : 'bg-primary/10 text-primary'
                "
              >
                <Icon
                  :icon="
                    selectedQueueAlbumMissingCount > 0
                      ? 'clarity:warning-line'
                      : 'clarity:check-line'
                  "
                  class="h-3.5 w-3.5"
                />
                {{
                  selectedQueueAlbumMissingCount > 0
                    ? t('player.albumMissingShort', {
                        count: selectedQueueAlbumMissingCount,
                      })
                    : t('player.albumComplete')
                }}
              </span>
            </div>

            <div class="track-modal-albums">
              <div class="mb-2 flex items-center justify-between gap-3">
                <h3 class="player-detail-heading">
                  {{ t('player.matchingAlbums') }}
                </h3>
                <span
                  v-if="queueAlbumLookupLoading"
                  class="loading loading-spinner loading-xs text-primary"
                />
              </div>
              <div v-if="queueAlbumCandidates.length" class="space-y-2">
                <article
                  v-for="album in queueAlbumCandidates"
                  :key="album.browse_id || album.url || album.name"
                  class="queue-album-card"
                >
                  <div class="queue-album-main">
                    <div class="queue-album-summary">
                      <div class="artist-result-cover">
                        <CoverImage
                          v-if="album.cover_url"
                          :src="
                            API.remoteCoverSources(album.cover_url, 160).src
                          "
                          :fallbacks="
                            API.remoteCoverSources(album.cover_url, 160)
                              .fallbacks
                          "
                          :alt="album.name"
                          eager
                          img-class="absolute inset-0 h-full w-full object-cover"
                        />
                      </div>
                      <div class="min-w-0 flex-1">
                        <p class="truncate text-sm font-semibold">
                          {{ album.name }}
                        </p>
                        <p class="truncate text-xs text-base-content/50">
                          {{ queueAlbumCandidateMeta(album) }}
                        </p>
                      </div>
                    </div>
                    <div class="queue-album-footer">
                      <p
                        class="queue-album-status"
                        :class="queueAlbumStatusClass(album)"
                      >
                        {{ queueAlbumStatusLabel(album) }}
                      </p>
                      <div class="queue-album-actions">
                        <button
                          type="button"
                          class="queue-album-action-btn"
                          :disabled="!album.browse_id"
                          @click="toggleQueueAlbumTracks(album)"
                        >
                          <span
                            v-if="queueAlbumTracksLoading[queueAlbumKey(album)]"
                            class="loading loading-spinner loading-xs"
                          />
                          <Icon
                            v-else
                            :icon="
                              expandedQueueAlbumKey === queueAlbumKey(album)
                                ? 'clarity:angle-line'
                                : 'clarity:angle-line'
                            "
                            class="h-3.5 w-3.5"
                            :class="{
                              'rotate-90':
                                expandedQueueAlbumKey !== queueAlbumKey(album),
                              '-rotate-90':
                                expandedQueueAlbumKey === queueAlbumKey(album),
                            }"
                          />
                          {{ t('player.viewAlbumTracks') }}
                        </button>
                        <button
                          type="button"
                          class="queue-album-action-btn queue-album-download-btn"
                          :class="downloadButtonClass(album)"
                          :title="t('player.downloadMissingAlbum')"
                          @click="downloadQueueAlbumMissing(album)"
                        >
                          <Icon
                            :icon="downloadButtonIcon(album)"
                            class="h-4 w-4"
                          />
                          {{ queueAlbumDownloadLabel(album) }}
                        </button>
                      </div>
                    </div>
                  </div>

                  <div
                    v-if="expandedQueueAlbumKey === queueAlbumKey(album)"
                    class="queue-album-tracks"
                  >
                    <div
                      v-if="queueAlbumTracksLoading[queueAlbumKey(album)]"
                      class="space-y-2"
                    >
                      <div
                        v-for="index in 4"
                        :key="index"
                        class="skeleton h-10 rounded-lg"
                      />
                    </div>
                    <div
                      v-else-if="queueAlbumTracks(album).length"
                      class="space-y-1.5"
                    >
                      <div class="queue-album-track-summary">
                        <span>
                          {{
                            t('player.albumTracksOwnedSummary', {
                              have: queueAlbumStatus(album).have,
                              total: queueAlbumStatus(album).total,
                            })
                          }}
                        </span>
                        <span
                          v-if="queueAlbumStatus(album).missing > 0"
                          class="text-amber-200"
                        >
                          {{
                            t('player.albumTracksMissingSummary', {
                              count: queueAlbumStatus(album).missing,
                            })
                          }}
                        </span>
                      </div>
                      <article
                        v-for="track in queueAlbumTracks(album)"
                        :key="track.song_id || track.url || track.name"
                        class="queue-album-track"
                      >
                        <div class="min-w-0 flex-1">
                          <p class="truncate text-sm font-medium">
                            {{ track.name }}
                          </p>
                          <p class="truncate text-xs text-base-content/45">
                            {{ resultArtistLabel(track) }}
                          </p>
                        </div>
                        <span
                          v-if="queueAlbumTrackOwned(track)"
                          class="queue-track-owned"
                        >
                          <Icon
                            icon="clarity:library-solid"
                            class="h-3.5 w-3.5"
                          />
                          {{ t('search.inLibrary') }}
                        </span>
                        <button
                          v-else
                          type="button"
                          class="queue-track-download"
                          :class="downloadButtonClass(track)"
                          :title="t('common.download')"
                          @click="downloadSimilarArtistItem(track)"
                        >
                          <Icon
                            :icon="downloadButtonIcon(track)"
                            class="h-3.5 w-3.5"
                          />
                          {{ t('player.missingTrack') }}
                        </button>
                      </article>
                    </div>
                    <p v-else class="player-detail-empty">
                      {{ t('player.albumTracksUnavailable') }}
                    </p>
                  </div>
                </article>
              </div>
              <p
                v-else-if="!queueAlbumLookupLoading"
                class="player-detail-empty"
              >
                {{ t('player.noMatchingAlbums') }}
              </p>
            </div>
          </div>
        </section>
      </div>
    </Teleport>

    <Teleport to="body">
      <div
        v-if="selectedSimilarTrack"
        class="artist-modal-backdrop"
        @click.self="closeSimilarTrack"
      >
        <section
          class="track-modal surface-strong"
          role="dialog"
          aria-modal="true"
          :aria-label="selectedSimilarTrack.name"
        >
          <header class="artist-modal-header">
            <h2 class="truncate text-lg font-bold">
              {{ t('player.trackDetails') }}
            </h2>
            <button
              type="button"
              class="icon-btn shrink-0"
              :title="t('common.close')"
              @click="closeSimilarTrack"
            >
              <Icon icon="clarity:close-line" class="h-5 w-5" />
            </button>
          </header>

          <div class="track-modal-body">
            <div class="track-modal-cover">
              <CoverImage
                v-if="selectedSimilarTrack.cover_url"
                :src="
                  API.remoteCoverSources(selectedSimilarTrack.cover_url, 480)
                    .src
                "
                :fallbacks="
                  API.remoteCoverSources(selectedSimilarTrack.cover_url, 480)
                    .fallbacks
                "
                :alt="selectedSimilarTrack.name"
                img-class="absolute inset-0 h-full w-full object-cover"
              >
                <template #fallback>
                  <Icon
                    icon="clarity:music-note-line"
                    class="h-12 w-12 text-base-content/35"
                  />
                </template>
              </CoverImage>
            </div>

            <div class="min-w-0 flex-1">
              <h3 class="text-xl font-bold leading-tight">
                {{ selectedSimilarTrack.name }}
              </h3>
              <p class="mt-1 text-sm text-base-content/65">
                {{ resultArtistLabel(selectedSimilarTrack) }}
              </p>
              <dl class="track-modal-metadata">
                <div v-if="selectedSimilarTrack.album_name">
                  <dt>{{ t('library.albums') }}</dt>
                  <dd>{{ selectedSimilarTrack.album_name }}</dd>
                </div>
                <div v-if="selectedSimilarTrack.year">
                  <dt>{{ t('player.releaseYear') }}</dt>
                  <dd>{{ selectedSimilarTrack.year }}</dd>
                </div>
                <div v-if="selectedSimilarTrack.duration">
                  <dt>{{ t('player.durationLabel') }}</dt>
                  <dd>{{ formatTime(selectedSimilarTrack.duration) }}</dd>
                </div>
              </dl>

              <div class="mt-5 flex flex-wrap items-center gap-2">
                <button
                  v-if="!similarTrackOwnership.isOwned(selectedSimilarTrack)"
                  type="button"
                  class="btn btn-primary btn-sm h-10 rounded-full px-4"
                  :class="downloadButtonClass(selectedSimilarTrack)"
                  @click="downloadSimilarArtistItem(selectedSimilarTrack)"
                >
                  <Icon
                    :icon="downloadButtonIcon(selectedSimilarTrack)"
                    class="h-4 w-4"
                  />
                  {{
                    downloadButtonState(selectedSimilarTrack) === 'loading'
                      ? t('common.downloading')
                      : downloadButtonState(selectedSimilarTrack) === 'done'
                        ? t('common.done')
                        : t('common.download')
                  }}
                </button>
                <span
                  v-else
                  class="btn btn-sm h-10 cursor-default rounded-full border-primary/25 bg-primary/10 px-4 text-primary"
                >
                  <Icon icon="clarity:library-solid" class="h-4 w-4" />
                  {{ t('search.inLibrary') }}
                </span>
                <a
                  v-if="selectedSimilarTrack.url"
                  class="btn btn-sm h-10 rounded-full border-white/10 bg-base-100/70 px-4"
                  :href="selectedSimilarTrack.url"
                  target="_blank"
                  rel="noopener"
                >
                  <Icon icon="clarity:pop-out-line" class="h-4 w-4" />
                  {{ t('player.openSource') }}
                </a>
              </div>
            </div>
          </div>
        </section>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import {
  ref,
  onMounted,
  onUnmounted,
  onActivated,
  computed,
  watch,
  nextTick,
} from 'vue'
import { Icon } from '@iconify/vue'
import Navbar from '/src/components/Navbar.vue'
import CoverImage from '/src/components/CoverImage.vue'
import LibraryArtistMonitor from '/src/components/LibraryArtistMonitor.vue'
import API from '/src/model/api'
import { beginAppLoading, endAppLoading } from '/src/model/appLoading'
import {
  albumKey,
  groupAlbums,
  groupArtists,
  libraryItemsEqual,
  normalizeLibraryItem,
} from '/src/model/library'
import {
  fetchLibraryItems,
  getInitialLibrarySnapshot,
  onLibraryChanged,
} from '/src/model/librarySession'
import { usePlayer, formatTime, trackInfoFromFile } from '/src/model/player'
import { useDownloadManager } from '/src/model/download'
import {
  findOwnedAlbum,
  findOwnedTrack,
  useLibraryOwnership,
} from '/src/model/libraryOwnership'
import { useAlbumTrackCounts } from '/src/model/albumTrackCounts'
import {
  consumePlayerNavigation,
  resolvePlayerBrowseState,
} from '/src/model/playerNavigation'
import {
  buildApiBaseUrl,
  getServerConfig,
  isCapacitorNative,
} from '/src/model/serverConnection'
import { useI18n } from '/src/i18n'

defineOptions({ name: 'Player' })

const LYRICS_OFFSET_KEY = 'downtify-player-lyrics-offset'
const GENRE_REFRESH_DELAYS_MS = [15000, 60000, 300000]
const PLAYBACK_REFRESH_DELAY_MS = 30000
const NATIVE_SIMILAR_MEDIA_DELAY_MS = 5000
const WEB_SIMILAR_MEDIA_DELAY_MS = 300

const playerServerKey = buildApiBaseUrl(getServerConfig())
const initialPlayerSnapshot = getInitialLibrarySnapshot(playerServerKey)

const { t } = useI18n()
const player = usePlayer()
const downloadManager = useDownloadManager()

const files = ref(initialPlayerSnapshot.paths)
const libraryItems = ref(initialPlayerSnapshot.items)
const loading = ref(!initialPlayerSnapshot.ready)
const progressBar = ref(null)
const progressTrack = ref(null)
const isScrubbing = ref(false)
const scrubPct = ref(0)
const lyricsOpen = ref(false)
const lyricsLoading = ref(false)
const syncedLyrics = ref([])
const lyricsPlain = ref('')
const lyricsScroller = ref(null)
const lyricLineRefs = ref([])
const lyricsOffset = ref(readLyricsOffset())
const similarArtists = ref([])
const similarArtistsLoading = ref(false)
const similarMediaTab = ref('artists')
const similarTracks = ref([])
const similarTracksLoading = ref(false)
const selectedSimilarTrack = ref(null)
const similarTrackOwnership = useLibraryOwnership(similarTracks)
const selectedSimilarArtist = ref(null)
const similarArtistDetailsLoading = ref(false)
const similarArtistResults = ref([])
const similarArtistTab = ref('albums')
const similarArtistAlbumCounts = useAlbumTrackCounts(
  () => similarArtistAlbums.value
)
const selectedQueueTrack = ref(null)
const queueAlbumCandidates = ref([])
const queueAlbumLookupLoading = ref(false)
const queueAlbumCounts = useAlbumTrackCounts(queueAlbumCandidates)
const downloadButtonStates = ref({})
const expandedQueueAlbumKey = ref('')
const queueAlbumTracksByKey = ref({})
const queueAlbumTracksLoading = ref({})
let lyricsRequestSeq = 0
let similarArtistsRequestSeq = 0
let similarTracksRequestSeq = 0
let queueAlbumLookupSeq = 0
let similarMediaDrag = null
let suppressSimilarClickUntil = 0
let seekRaf = 0
let pendingSeekRatio = null

const displayProgressPct = computed(() =>
  isScrubbing.value ? scrubPct.value : player.progressPct.value
)

function startSimilarMediaDrag(event) {
  if (event.pointerType !== 'mouse' || event.button !== 0) return
  const scroller = event.currentTarget
  similarMediaDrag = {
    scroller,
    pointerId: event.pointerId,
    startX: event.clientX,
    startScrollLeft: scroller.scrollLeft,
    moved: false,
  }
}

function moveSimilarMediaDrag(event) {
  const drag = similarMediaDrag
  if (!drag || drag.pointerId !== event.pointerId) return
  const distance = event.clientX - drag.startX
  if (!drag.moved && Math.abs(distance) > 8) {
    drag.moved = true
    drag.scroller.setPointerCapture?.(event.pointerId)
    drag.scroller.classList.add('is-dragging')
  }
  if (!drag.moved) return
  drag.scroller.scrollLeft = drag.startScrollLeft - distance
  event.preventDefault()
}

function endSimilarMediaDrag(event) {
  const drag = similarMediaDrag
  if (!drag || drag.pointerId !== event.pointerId) return
  drag.scroller.classList.remove('is-dragging')
  if (drag.moved) {
    drag.scroller.releasePointerCapture?.(event.pointerId)
    suppressSimilarClickUntil = performance.now() + 100
  }
  similarMediaDrag = null
}

function suppressSimilarMediaClick(event) {
  if (performance.now() >= suppressSimilarClickUntil) return
  event.preventDefault()
  event.stopPropagation()
}
let genreRefreshTimers = []
let deferredLibraryRefreshTimer = 0
let similarArtistsTimer = 0
let similarTracksTimer = 0
let stopLibraryListener = null

const unknownGenreLabel = computed(() => t('player.unknownGenre'))
const libraryGroupOptions = computed(() => ({
  unknownArtist: t('common.unknownArtist'),
}))

const artists = computed(() =>
  groupArtists(libraryItems.value, libraryGroupOptions.value)
)
const albums = computed(() =>
  groupAlbums(libraryItems.value, libraryGroupOptions.value)
)

const hasActiveTrack = computed(
  () => player.currentIndex.value >= 0 && !!player.currentTrack.value
)

const lyricsAvailable = computed(
  () => syncedLyrics.value.length > 0 || Boolean(lyricsPlain.value)
)

const syncedLyricsTime = computed(() =>
  Math.max(0, player.currentTime.value + lyricsOffset.value)
)

const lyricsOffsetLabel = computed(() => {
  const offset = lyricsOffset.value
  if (Math.abs(offset) < 0.05) return '0.0s'
  return `${offset > 0 ? '+' : ''}${offset.toFixed(1)}s`
})

const activeLyricIndex = computed(() => {
  const lines = syncedLyrics.value
  if (!lines.length) return -1
  const current = syncedLyricsTime.value
  let active = 0
  for (let i = 0; i < lines.length; i += 1) {
    if (Number(lines[i]?.time || 0) > current) break
    active = i
  }
  return active
})

const currentLibraryItem = computed(() => {
  const file = player.currentTrack.value?.file
  if (!file) return null
  return libraryItems.value.find((item) => item.file === file) || null
})

const upNextTracks = computed(() => {
  return player.upNext.value || []
})

const queueDisplayTracks = computed(() => {
  if (upNextTracks.value.length) return upNextTracks.value
  const current = player.currentIndex.value
  if (current < 0 || player.playlist.value.length <= 1) return []
  return player.playlist.value
    .map((track, index) => ({ track, index, offset: index + 1 }))
    .filter((item) => item.index !== current)
})

const visibleQueueTracks = computed(() => queueDisplayTracks.value.slice(0, 6))

const selectedQueueTrackLibraryItem = computed(() => {
  const file = selectedQueueTrack.value?.track?.file
  if (!file) return null
  return libraryItems.value.find((item) => item.file === file) || null
})

const selectedQueueAlbum = computed(() => {
  const item = selectedQueueTrackLibraryItem.value
  if (!item?.album) return null
  const key = albumKey(item.artist, item.album)
  return albums.value.find((album) => album.key === key) || null
})

const bestQueueAlbumCandidate = computed(() => {
  const local = selectedQueueAlbum.value
  if (!local) return null
  const localName = normalizedArtistKey(local.name)
  const localArtist = normalizedArtistKey(local.artist)
  return (
    queueAlbumCandidates.value.find((album) => {
      const name = normalizedArtistKey(album?.name)
      const artist = normalizedArtistKey(resultArtistLabel(album))
      return (
        name === localName && (!localArtist || artist.includes(localArtist))
      )
    }) ||
    queueAlbumCandidates.value[0] ||
    null
  )
})

const selectedQueueAlbumExpectedCount = computed(() => {
  const count = queueAlbumCounts.trackCountFor(bestQueueAlbumCandidate.value)
  return count || Number(bestQueueAlbumCandidate.value?.track_count) || 0
})

const selectedQueueAlbumMissingCount = computed(() => {
  const local = selectedQueueAlbum.value
  const expected = selectedQueueAlbumExpectedCount.value
  if (!local || !expected) return 0
  return Math.max(0, expected - local.files.length)
})

function artistNamesMatch(a, b) {
  return (
    String(a || '')
      .trim()
      .toLocaleLowerCase() ===
    String(b || '')
      .trim()
      .toLocaleLowerCase()
  )
}

const currentArtistEntry = computed(() => {
  const name =
    currentLibraryItem.value?.artist || player.currentTrack.value?.artist || ''
  if (!name) return null
  return (
    artists.value.find((artist) => artistNamesMatch(artist.name, name)) || null
  )
})

const currentArtistName = computed(
  () =>
    currentLibraryItem.value?.artist || player.currentTrack.value?.artist || ''
)

async function loadSimilarArtists(artistName) {
  similarArtistsRequestSeq += 1
  const seq = similarArtistsRequestSeq
  similarArtists.value = []
  similarArtistsLoading.value = Boolean(artistName)
  if (!artistName) return

  try {
    const res = await API.getSimilarArtists(artistName)
    if (seq !== similarArtistsRequestSeq) return
    similarArtists.value = Array.isArray(res.data?.artists)
      ? res.data.artists
      : []
  } catch {
    // Older connected servers do not expose the dedicated endpoint yet.
  }

  if (seq === similarArtistsRequestSeq && !similarArtists.value.length) {
    similarArtists.value = await searchSimilarArtistFallback(artistName)
  }
  if (seq === similarArtistsRequestSeq && !similarArtists.value.length) {
    similarArtists.value = librarySimilarArtistFallback(artistName)
  }

  if (seq === similarArtistsRequestSeq) {
    similarArtistsLoading.value = false
  }
}

function scheduleSimilarArtistsLoad(artistName) {
  if (similarArtistsTimer) clearTimeout(similarArtistsTimer)
  const delay = isCapacitorNative()
    ? NATIVE_SIMILAR_MEDIA_DELAY_MS
    : WEB_SIMILAR_MEDIA_DELAY_MS
  similarArtistsTimer = setTimeout(() => {
    similarArtistsTimer = 0
    void loadSimilarArtists(artistName)
  }, delay)
}

function normalizedArtistKey(name) {
  return String(name || '')
    .trim()
    .toLocaleLowerCase()
}

function appendSimilarArtist(results, seen, artist) {
  const name = String(artist?.name || '').trim()
  const key = normalizedArtistKey(name)
  if (!name || seen.has(key)) return
  seen.add(key)
  results.push({ ...artist, name })
}

async function searchSimilarArtistFallback(artistName) {
  const target = normalizedArtistKey(artistName)
  const seen = new Set([target])
  const results = []
  try {
    const response = await API.search(artistName)
    for (const item of Array.isArray(response.data) ? response.data : []) {
      const names = Array.isArray(item?.artists)
        ? item.artists
        : String(item?.artist || '')
            .split(',')
            .map((name) => name.trim())
      for (const name of names) {
        appendSimilarArtist(results, seen, {
          name,
          browse_id: '',
          image_url: item?.cover_url || '',
          source: 'search',
        })
        if (results.length >= 8) return results
      }
    }
  } catch {
    // The downloaded library remains available as the final fallback.
  }
  return results
}

function librarySimilarArtistFallback(artistName) {
  const seen = new Set([normalizedArtistKey(artistName)])
  const results = []
  for (const artist of artists.value) {
    const cover = artistCoverFor(artist)
    appendSimilarArtist(results, seen, {
      name: artist.name,
      browse_id: '',
      image_url: cover.src || cover.fallbacks?.[0] || '',
      source: 'library',
    })
    if (results.length >= 8) break
  }
  return results
}

function similarArtistCoverSources(artist) {
  const remote = String(artist?.image_url || '').trim()
  const remoteSources = /^https?:\/\//i.test(remote)
    ? API.remoteCoverSources(remote, 192)
    : { src: API.apiAssetUrl(remote), fallbacks: [] }
  const libraryArtist = artists.value.find((entry) =>
    artistNamesMatch(entry.name, artist?.name)
  )
  const local = libraryArtist
    ? artistCoverFor(libraryArtist)
    : { src: '', fallbacks: [] }
  const candidates = [
    remoteSources.src,
    ...(remoteSources.fallbacks || []),
    local.src,
    ...(local.fallbacks || []),
  ].filter(Boolean)
  return {
    src: candidates[0] || '',
    fallbacks: [...new Set(candidates.slice(1))],
  }
}

function isSimilarArtistOwned(artist) {
  return artists.value.some((entry) =>
    artistNamesMatch(entry.name, artist?.name)
  )
}

const similarArtistAlbums = computed(() =>
  similarArtistResults.value.filter((item) => item?.media_type === 'album')
)

const similarArtistTracks = computed(() =>
  similarArtistResults.value.filter((item) => item?.media_type !== 'album')
)

const visibleSimilarArtistResults = computed(() =>
  similarArtistTab.value === 'albums'
    ? similarArtistAlbums.value
    : similarArtistTracks.value
)

async function openSimilarArtist(artist) {
  selectedSimilarArtist.value = artist
  similarArtistDetailsLoading.value = true
  similarArtistResults.value = []
  similarArtistTab.value = 'albums'
  try {
    const response = await API.search(artist.name)
    if (selectedSimilarArtist.value !== artist) return
    similarArtistResults.value = Array.isArray(response.data)
      ? response.data
      : []
    if (!similarArtistAlbums.value.length && similarArtistTracks.value.length) {
      similarArtistTab.value = 'tracks'
    }
  } catch {
    if (selectedSimilarArtist.value === artist) similarArtistResults.value = []
  } finally {
    if (selectedSimilarArtist.value === artist) {
      similarArtistDetailsLoading.value = false
    }
  }
}

function closeSimilarArtist() {
  selectedSimilarArtist.value = null
  similarArtistResults.value = []
  similarArtistDetailsLoading.value = false
}

function resultArtistLabel(item) {
  if (Array.isArray(item?.artists)) return item.artists.join(', ')
  return String(item?.artist || item?.album_name || '')
}

function similarArtistAlbumTrackCountLabel(album) {
  const count = similarArtistAlbumCounts.trackCountFor(album)
  if (!count) return ''
  return t(count === 1 ? 'player.countOne' : 'player.countMany', { count })
}

function queueTrackArtist(track) {
  const item = libraryItems.value.find((entry) => entry.file === track?.file)
  return item?.artist || track?.artist || t('common.unknownArtist')
}

function queueAlbumCandidateMeta(album) {
  const count = queueAlbumCounts.trackCountFor(album)
  const artist = resultArtistLabel(album)
  const countLabel = count ? t('player.countMany', { count }) : ''
  return [artist, countLabel].filter(Boolean).join(' - ')
}

function queueAlbumKey(album) {
  return String(album?.browse_id || album?.url || album?.name || '').trim()
}

function queueAlbumTracks(album) {
  return queueAlbumTracksByKey.value[queueAlbumKey(album)] || []
}

function queueAlbumOwnedAlbum(album) {
  return findOwnedAlbum(album, libraryItems.value)
}

function queueAlbumTrackOwned(track) {
  return Boolean(findOwnedTrack(track, libraryItems.value))
}

function queueAlbumMissingTracks(album) {
  return queueAlbumTracks(album).filter((track) => !queueAlbumTrackOwned(track))
}

function queueAlbumStatus(album) {
  const tracks = queueAlbumTracks(album)
  const expected = queueAlbumCounts.trackCountFor(album)
  const ownedAlbum = queueAlbumOwnedAlbum(album)
  if (tracks.length) {
    const missing = queueAlbumMissingTracks(album).length
    return {
      owned: missing === 0,
      missing,
      have: tracks.length - missing,
      total: tracks.length,
    }
  }
  if (ownedAlbum && expected) {
    const missing = Math.max(0, expected - ownedAlbum.files.length)
    return {
      owned: missing === 0,
      missing,
      have: ownedAlbum.files.length,
      total: expected,
    }
  }
  if (ownedAlbum) {
    return {
      owned: true,
      missing: 0,
      have: ownedAlbum.files.length,
      total: ownedAlbum.files.length,
    }
  }
  return { owned: false, missing: 0, have: 0, total: expected || 0 }
}

function queueAlbumStatusLabel(album) {
  const status = queueAlbumStatus(album)
  if (status.owned) return t('player.albumDownloaded')
  if (status.total) {
    return t('player.albumCompleteness', {
      have: status.have,
      total: status.total,
    })
  }
  return t('player.albumNotDownloaded')
}

function queueAlbumDownloadLabel(album) {
  const status = queueAlbumStatus(album)
  if (status.have > 0 && status.missing > 0) {
    return t('player.downloadMissing')
  }
  return t('player.downloadAlbum')
}

function queueAlbumStatusClass(album) {
  const status = queueAlbumStatus(album)
  if (status.owned) return 'text-primary'
  if (status.have > 0) return 'text-amber-200'
  return 'text-base-content/45'
}

async function loadQueueAlbumTracks(album) {
  const key = queueAlbumKey(album)
  if (!key || queueAlbumTracksByKey.value[key]?.length) return
  if (!album?.browse_id) return
  queueAlbumTracksLoading.value = {
    ...queueAlbumTracksLoading.value,
    [key]: true,
  }
  try {
    const response = await API.openYoutubeAlbum(album.browse_id)
    queueAlbumTracksByKey.value = {
      ...queueAlbumTracksByKey.value,
      [key]: Array.isArray(response.data) ? response.data : [],
    }
  } catch {
    queueAlbumTracksByKey.value = {
      ...queueAlbumTracksByKey.value,
      [key]: [],
    }
  } finally {
    queueAlbumTracksLoading.value = {
      ...queueAlbumTracksLoading.value,
      [key]: false,
    }
  }
}

function toggleQueueAlbumTracks(album) {
  const key = queueAlbumKey(album)
  if (!key) return
  expandedQueueAlbumKey.value = expandedQueueAlbumKey.value === key ? '' : key
  if (expandedQueueAlbumKey.value) {
    void loadQueueAlbumTracks(album)
  }
}

async function downloadQueueAlbumMissing(album) {
  await loadQueueAlbumTracks(album)
  const missing = queueAlbumMissingTracks(album)
  if (!missing.length) {
    await downloadSimilarArtistItem(album)
    return
  }
  setDownloadButtonState(album, 'loading')
  try {
    await downloadManager.queueBatch(missing)
    setDownloadButtonState(album, 'done')
    setTimeout(() => clearDownloadButtonState(album), 1400)
  } catch {
    clearDownloadButtonState(album)
  }
}

async function loadQueueAlbumCandidates(trackItem) {
  queueAlbumLookupSeq += 1
  const seq = queueAlbumLookupSeq
  queueAlbumCandidates.value = []
  expandedQueueAlbumKey.value = ''
  queueAlbumTracksByKey.value = {}
  queueAlbumTracksLoading.value = {}
  const libraryItem =
    libraryItems.value.find((item) => item.file === trackItem?.track?.file) ||
    null
  const query = [
    libraryItem?.artist || queueTrackArtist(trackItem?.track),
    libraryItem?.album,
  ]
    .filter(Boolean)
    .join(' ')
  queueAlbumLookupLoading.value = Boolean(query)
  if (!query) return

  try {
    const response = await API.search(query)
    if (seq !== queueAlbumLookupSeq) return
    queueAlbumCandidates.value = (
      Array.isArray(response.data) ? response.data : []
    )
      .filter((item) => item?.media_type === 'album')
      .slice(0, 5)
  } catch {
    if (seq === queueAlbumLookupSeq) queueAlbumCandidates.value = []
  } finally {
    if (seq === queueAlbumLookupSeq) queueAlbumLookupLoading.value = false
  }
}

function openQueueTrack(item) {
  selectedQueueTrack.value = item
  void loadQueueAlbumCandidates(item)
}

function closeQueueTrack() {
  selectedQueueTrack.value = null
  queueAlbumCandidates.value = []
  queueAlbumLookupLoading.value = false
  expandedQueueAlbumKey.value = ''
  queueAlbumTracksByKey.value = {}
  queueAlbumTracksLoading.value = {}
}

function downloadButtonKey(item) {
  return [
    item?.media_type || 'track',
    item?.browse_id,
    item?.song_id,
    item?.url,
    item?.name,
    resultArtistLabel(item),
  ]
    .filter(Boolean)
    .join(':')
}

function setDownloadButtonState(item, state) {
  const key = downloadButtonKey(item)
  if (!key) return
  downloadButtonStates.value = {
    ...downloadButtonStates.value,
    [key]: state,
  }
}

function clearDownloadButtonState(item) {
  const key = downloadButtonKey(item)
  if (!key || !downloadButtonStates.value[key]) return
  const next = { ...downloadButtonStates.value }
  delete next[key]
  downloadButtonStates.value = next
}

function downloadButtonState(item) {
  const key = downloadButtonKey(item)
  return key ? downloadButtonStates.value[key] || '' : ''
}

function downloadButtonClass(item) {
  const state = downloadButtonState(item)
  return {
    'download-button-loading': state === 'loading',
    'download-button-done': state === 'done',
  }
}

function downloadButtonIcon(item) {
  const state = downloadButtonState(item)
  if (state === 'loading') return 'clarity:sync-line'
  if (state === 'done') return 'clarity:check-line'
  return 'clarity:download-line'
}

async function downloadSimilarArtistItem(item) {
  if (!item || downloadButtonState(item) === 'loading') return
  setDownloadButtonState(item, 'loading')
  try {
    await downloadManager.queue(item)
    setDownloadButtonState(item, 'done')
    setTimeout(() => clearDownloadButtonState(item), 1400)
  } catch {
    clearDownloadButtonState(item)
  }
}

function openSimilarTrack(track) {
  selectedSimilarTrack.value = track
}

function closeSimilarTrack() {
  selectedSimilarTrack.value = null
}

async function loadSimilarTracks(title, artistName) {
  similarTracksRequestSeq += 1
  const seq = similarTracksRequestSeq
  similarTracks.value = []
  similarTracksLoading.value = Boolean(title || artistName)
  if (!title && !artistName) return

  try {
    const response = await API.search(
      [title, artistName].filter(Boolean).join(' ')
    )
    if (seq !== similarTracksRequestSeq) return
    const currentTitleKey = String(title || '')
      .trim()
      .toLocaleLowerCase()
    const seen = new Set()
    similarTracks.value = (Array.isArray(response.data) ? response.data : [])
      .filter((item) => item?.media_type !== 'album')
      .filter((item) => {
        const key = String(item?.song_id || item?.url || '').trim()
        const itemTitle = String(item?.name || '')
          .trim()
          .toLocaleLowerCase()
        if (!key || seen.has(key) || itemTitle === currentTitleKey) return false
        seen.add(key)
        return true
      })
      .slice(0, 16)
  } catch {
    if (seq === similarTracksRequestSeq) similarTracks.value = []
  } finally {
    if (seq === similarTracksRequestSeq) similarTracksLoading.value = false
  }
}

function scheduleSimilarTracksLoad(title, artistName) {
  if (similarTracksTimer) clearTimeout(similarTracksTimer)
  const delay = isCapacitorNative()
    ? NATIVE_SIMILAR_MEDIA_DELAY_MS
    : WEB_SIMILAR_MEDIA_DELAY_MS
  similarTracksTimer = setTimeout(() => {
    similarTracksTimer = 0
    void loadSimilarTracks(title, artistName)
  }, delay)
}

const currentAlbumKey = computed(() => {
  const item = currentLibraryItem.value
  if (!item?.album) return ''
  return albumKey(item.artist, item.album)
})

const currentArtistAlbums = computed(() => {
  const entry = currentArtistEntry.value
  if (!entry) return []
  return albums.value.filter((album) =>
    artistNamesMatch(album.artist, entry.name)
  )
})

const currentCoverSources = computed(() => {
  const file = player.currentTrack.value?.file || ''
  const artist =
    currentLibraryItem.value?.artist || player.currentTrack.value?.artist || ''
  return API.coverSourcesForNowPlaying(file, { artistName: artist })
})

const artistCoverMap = computed(() => {
  const map = new Map()
  for (const artist of artists.value) {
    map.set(
      artist.name,
      API.coverSourcesForArtist(artist.name, artist.previewFiles)
    )
  }
  return map
})

function artistCoverFor(artist) {
  return artistCoverMap.value.get(artist?.name) || API.coverSourcesForArtist('')
}

function coverSourcesFor(file) {
  return API.coverSourcesForFile(file)
}

function readLyricsOffset() {
  try {
    const value = Number.parseFloat(
      localStorage.getItem(LYRICS_OFFSET_KEY) || '0'
    )
    return Number.isFinite(value) ? Math.max(-5, Math.min(5, value)) : 0
  } catch {
    return 0
  }
}

function persistLyricsOffset() {
  try {
    localStorage.setItem(LYRICS_OFFSET_KEY, lyricsOffset.value.toFixed(1))
  } catch {
    // Ignore private-mode storage errors.
  }
}

function adjustLyricsOffset(delta) {
  const next = Math.round((lyricsOffset.value + delta) * 10) / 10
  lyricsOffset.value = Math.max(-5, Math.min(5, next))
  persistLyricsOffset()
}

function resetLyricsOffset() {
  lyricsOffset.value = 0
  persistLyricsOffset()
}

function setLyricLineRef(el, index) {
  if (el) lyricLineRefs.value[index] = el
}

function centerActiveLyric(index) {
  const scroller = lyricsScroller.value
  const line = lyricLineRefs.value[index]
  if (!scroller || !line) return
  const target =
    line.offsetTop -
    scroller.offsetTop -
    scroller.clientHeight / 2 +
    line.clientHeight / 2
  scroller.scrollTo({
    top: Math.max(0, target),
    behavior: 'smooth',
  })
}

async function loadLyricsForFile(file) {
  lyricsRequestSeq += 1
  const seq = lyricsRequestSeq
  syncedLyrics.value = []
  lyricsPlain.value = ''
  lyricLineRefs.value = []
  lyricsLoading.value = Boolean(file)
  if (!file) {
    lyricsOpen.value = false
    lyricsLoading.value = false
    return
  }

  try {
    const res = await API.getLibraryLyrics(file)
    if (seq !== lyricsRequestSeq) return
    const data = res.data || {}
    syncedLyrics.value = Array.isArray(data.lines) ? data.lines : []
    lyricsPlain.value = syncedLyrics.value.length
      ? ''
      : String(data.plain || '').trim()
    if (!lyricsAvailable.value) lyricsOpen.value = false
  } catch {
    if (seq !== lyricsRequestSeq) return
    syncedLyrics.value = []
    lyricsPlain.value = ''
    lyricsOpen.value = false
  } finally {
    if (seq === lyricsRequestSeq) {
      lyricsLoading.value = false
    }
  }
}

function fallbackLibraryItems(paths) {
  const options = libraryGroupOptions.value
  return (paths || []).map((file) => {
    const info = trackInfoFromFile(file)
    return normalizeLibraryItem(
      {
        file,
        title: info.title,
        artist: info.artist,
        album: '',
        genre: '',
      },
      options
    )
  })
}

function syncPlayerPlaylist(fileList) {
  player.syncPlaylistFromFiles(fileList || [], { autoplay: false })
}

function libraryPathsUnchanged(nextItems) {
  const nextPaths = (nextItems || []).map((item) => item.file)
  if (nextPaths.length !== files.value.length) return false
  return nextPaths.every((file, index) => file === files.value[index])
}

function applyLibraryItems(items) {
  const options = libraryGroupOptions.value
  libraryItems.value = items.map((item) => normalizeLibraryItem(item, options))
  files.value = libraryItems.value.map((item) => item.file)
  warmPlayerLibraryCovers()
}

function hydrateLibraryFromSession() {
  const snapshot = getInitialLibrarySnapshot(playerServerKey)
  if (!snapshot.ready) return false

  libraryItems.value = snapshot.items.map((item) =>
    normalizeLibraryItem(item, libraryGroupOptions.value)
  )
  files.value = snapshot.paths

  if (player.playlist.value.length === 0 && files.value.length > 0) {
    syncPlayerPlaylist(files.value)
  } else if (player.currentTrack.value?.file && files.value.length > 0) {
    syncPlayerPlaylist(files.value)
  }

  warmPlayerLibraryCovers()
  return true
}

function warmPlayerLibraryCovers() {
  if (isCapacitorNative() && player.isPlaying.value) return
  API.warmLibraryCovers(libraryItems.value)
}

async function fetchPlayerLibraryItems(options = {}) {
  return fetchLibraryItems(
    () => API.getLibraryFiles().then((res) => res.data || []),
    options
  )
}

async function applyFetchedLibrary(items) {
  if (!items.length) {
    libraryItems.value = []
    files.value = []
    return
  }

  applyLibraryItems(items)
  syncPlayerPlaylist(items.map((item) => item.file))
}

function deferLibraryMetadataRefresh(force = false) {
  if (deferredLibraryRefreshTimer) {
    clearTimeout(deferredLibraryRefreshTimer)
  }
  deferredLibraryRefreshTimer = setTimeout(() => {
    deferredLibraryRefreshTimer = 0
    void refreshLibraryMetadataInBackground(force)
  }, PLAYBACK_REFRESH_DELAY_MS)
}

async function refreshLibraryMetadataInBackground(force = false) {
  if (player.isPlaying.value) {
    deferLibraryMetadataRefresh(force)
    return
  }
  try {
    const items = await API.refreshLibraryInBackground(force, {
      warmCovers: !(isCapacitorNative() && player.isPlaying.value),
    })
    if (items.length > 0 && !libraryItemsUnchanged(items)) {
      applyLibraryItems(items)
      if (!libraryPathsUnchanged(items)) {
        syncPlayerPlaylist(items.map((item) => item.file))
      }
      scheduleGenreRefresh(items)
    } else if (items.length > 0) {
      scheduleGenreRefresh(items)
    }
  } catch {
    // Ignore background refresh failures.
  }
}

function libraryItemsUnchanged(nextItems) {
  const options = libraryGroupOptions.value
  const normalized = nextItems.map((item) =>
    normalizeLibraryItem(item, options)
  )
  return libraryItemsEqual(libraryItems.value, normalized)
}

function countUnknownGenres(items) {
  const label = unknownGenreLabel.value
  return (items || []).filter((item) => {
    const genre = String(item?.genre || '').trim()
    return !genre || genre === label
  }).length
}

function clearGenreRefreshTimers() {
  for (const timer of genreRefreshTimers) {
    clearTimeout(timer)
  }
  genreRefreshTimers = []
}

async function refreshLibraryMetadata() {
  await refreshLibraryMetadataInBackground()
}

async function refreshLibraryGenres() {
  await refreshLibraryMetadata()
}

function scheduleGenreRefresh(items) {
  clearGenreRefreshTimers()
  if (countUnknownGenres(items) === 0) return

  for (const delay of GENRE_REFRESH_DELAYS_MS) {
    genreRefreshTimers.push(
      setTimeout(() => {
        refreshLibraryGenres()
      }, delay)
    )
  }
}

async function load({ background = false } = {}) {
  const hadCache =
    hydrateLibraryFromSession() ||
    files.value.length > 0 ||
    libraryItems.value.length > 0
  if (!background) {
    loading.value = !hadCache
    if (!hadCache) beginAppLoading()
  }

  try {
    const items = await fetchPlayerLibraryItems({
      preferPrefetch: !background,
    })
    await applyFetchedLibrary(items)
  } catch {
    try {
      const res = await API.listDownloads()
      const paths = res.data || []
      if (paths.length > 0) {
        applyLibraryItems(fallbackLibraryItems(paths))
        syncPlayerPlaylist(paths)
      } else {
        files.value = []
        libraryItems.value = []
      }
    } catch {
      if (!hadCache) {
        files.value = []
        libraryItems.value = []
      }
    }
  } finally {
    loading.value = false
    if (!background && !hadCache) endAppLoading()
    applyPlayerNavigationIntent()
    if (player.currentTrack.value?.file && files.value.length > 0) {
      syncPlayerPlaylist(files.value)
    }
  }

  if (countUnknownGenres(libraryItems.value) > 0) {
    scheduleGenreRefresh(libraryItems.value)
  }
}

function playFiles(fileList, startFile = null, context = null) {
  const list = fileList || []
  if (!list.length) return
  const startIndex = startFile ? Math.max(0, list.indexOf(startFile)) : 0
  player.setPlaylist(list, { startIndex, context })
}

function applyPlayerNavigationIntent() {
  const intent = consumePlayerNavigation()
  if (!intent) return

  const state = resolvePlayerBrowseState(
    libraryItems.value,
    intent,
    libraryGroupOptions.value
  )
  if (!state) return

  playFiles(state.playlistFiles, state.startFile, state.context || null)
}

const trackTitle = computed(() => {
  if (!hasActiveTrack.value) return t('player.nothingPlaying')
  return player.currentTrack.value?.title || t('player.empty')
})

const trackArtist = computed(() => {
  if (!hasActiveTrack.value) return ''
  const c = player.currentTrack.value
  if (c?.artist) return c.artist
  return t('common.unknownArtist')
})

const playerContextIcon = computed(() => {
  const type = player.playlistContext.value?.type
  if (type === 'genre') return 'clarity:tag-line'
  if (type === 'artist') return 'clarity:user-line'
  if (type === 'album') return 'clarity:album-line'
  return 'clarity:playlist-line'
})

const playerContextLabel = computed(() => {
  const context = player.playlistContext.value
  if (!context?.type || !context?.name) return ''
  const count = player.playlist.value.length
  const countLabel = t(count === 1 ? 'player.countOne' : 'player.countMany', {
    count,
  })
  if (['genre', 'artist', 'album'].includes(context.type)) {
    return `${context.name} - ${countLabel}`
  }
  return ''
})

const repeatTitle = computed(() => {
  if (player.repeatMode.value === 'one') return t('player.repeatOne')
  if (player.repeatMode.value === 'all') return t('player.repeatAll')
  return t('player.repeatOff')
})

function onVolume(e) {
  player.setVolume(parseFloat(e.target.value))
}

function ratioFromEvent(e) {
  const el = progressTrack.value || progressBar.value
  if (!el) return 0
  const rect = el.getBoundingClientRect()
  if (rect.width <= 0) return 0
  const x = (e.clientX ?? 0) - rect.left
  return Math.max(0, Math.min(1, x / rect.width))
}

function flushPendingSeek() {
  if (pendingSeekRatio === null) return
  player.seekRatio(pendingSeekRatio)
  pendingSeekRatio = null
}

function queueSeek(ratio) {
  pendingSeekRatio = ratio
  if (seekRaf) return
  seekRaf = requestAnimationFrame(() => {
    seekRaf = 0
    flushPendingSeek()
  })
}

function applyScrub(e, { commitAudio = true } = {}) {
  const ratio = ratioFromEvent(e)
  scrubPct.value = ratio * 100
  if (commitAudio) {
    queueSeek(ratio)
  }
}

function onSeekStart(e) {
  if (!hasActiveTrack.value) return
  if (e.pointerType === 'mouse' && e.button !== 0) return
  e.preventDefault()
  isScrubbing.value = true
  const el = progressBar.value
  if (el?.setPointerCapture) {
    try {
      el.setPointerCapture(e.pointerId)
    } catch {
      // ignore
    }
  }
  applyScrub(e)
  window.addEventListener('pointermove', onSeekDrag)
  window.addEventListener('pointerup', onSeekEnd)
  window.addEventListener('pointercancel', onSeekEnd)
}

function onSeekDrag(e) {
  if (!isScrubbing.value) return
  applyScrub(e)
}

function onSeekEnd(e) {
  if (!isScrubbing.value) return
  isScrubbing.value = false
  if (e) {
    applyScrub(e)
  }
  flushPendingSeek()
  window.removeEventListener('pointermove', onSeekDrag)
  window.removeEventListener('pointerup', onSeekEnd)
  window.removeEventListener('pointercancel', onSeekEnd)
  const el = progressBar.value
  if (el?.releasePointerCapture && e?.pointerId !== undefined) {
    try {
      el.releasePointerCapture(e.pointerId)
    } catch {
      // ignore
    }
  }
}

function onSeekKeydown(e) {
  if (!player.duration.value) return
  const step = e.shiftKey ? 10 : 5
  if (e.key === 'ArrowLeft' || e.key === 'ArrowDown') {
    e.preventDefault()
    player.seek(Math.max(0, player.currentTime.value - step))
  } else if (e.key === 'ArrowRight' || e.key === 'ArrowUp') {
    e.preventDefault()
    player.seek(
      Math.min(player.duration.value, player.currentTime.value + step)
    )
  } else if (e.key === 'Home') {
    e.preventDefault()
    player.seek(0)
  } else if (e.key === 'End') {
    e.preventDefault()
    player.seek(player.duration.value)
  }
}

watch(
  () => player.currentTrack.value?.file || '',
  (file) => {
    void loadLyricsForFile(file)
  },
  { immediate: true }
)

watch(
  currentArtistName,
  (artistName) => {
    scheduleSimilarArtistsLoad(artistName)
  },
  { immediate: true }
)

watch(
  () => [
    player.currentTrack.value?.title || '',
    currentArtistName.value,
    player.currentTrack.value?.file || '',
  ],
  ([title, artistName, file]) => {
    const resolvedTitle = title || trackInfoFromFile(file).title
    scheduleSimilarTracksLoad(resolvedTitle, artistName)
  },
  { immediate: true }
)

watch(activeLyricIndex, async (index) => {
  if (!lyricsOpen.value || index < 0) return
  await nextTick()
  centerActiveLyric(index)
})

onMounted(() => {
  window.scroll(0, 0)
  if (libraryItems.value.length) {
    warmPlayerLibraryCovers()
    syncPlayerPlaylist(files.value)
  }
  load()
  stopLibraryListener = onLibraryChanged(() => {
    void refreshLibraryMetadataInBackground(true)
  })
})

onActivated(() => {
  if (libraryItems.value.length > 0) {
    syncPlayerPlaylist(files.value)
    applyPlayerNavigationIntent()
    void refreshLibraryMetadataInBackground()
    return
  }
  void load()
})

onUnmounted(() => {
  stopLibraryListener?.()
  clearGenreRefreshTimers()
  if (similarArtistsTimer) {
    clearTimeout(similarArtistsTimer)
    similarArtistsTimer = 0
  }
  if (similarTracksTimer) {
    clearTimeout(similarTracksTimer)
    similarTracksTimer = 0
  }
  if (deferredLibraryRefreshTimer) {
    clearTimeout(deferredLibraryRefreshTimer)
    deferredLibraryRefreshTimer = 0
  }
  onSeekEnd()
  if (seekRaf) {
    cancelAnimationFrame(seekRaf)
    seekRaf = 0
  }
})
</script>

<style scoped>
.player-view {
  @apply flex min-h-0 flex-col overflow-x-hidden;
}

.player-content {
  @apply flex min-w-0 flex-col gap-4 overflow-x-hidden sm:gap-6;
}

.player-shell,
.player-shell > section,
.player-shell > aside,
.player-now {
  min-width: 0;
  width: 100%;
  max-width: 100%;
}

.player-cover {
  width: auto;
  height: auto;
  max-width: 100%;
  aspect-ratio: 1 / 1;
  background: transparent;
  box-shadow: none;
  overflow: visible;
}

.player-cover-active {
  filter: drop-shadow(0 0 24px rgb(26 208 92 / 0.18));
}

.player-cover-active::before {
  content: '';
  position: absolute;
  inset: -18%;
  z-index: 0;
  border-radius: inherit;
  background: radial-gradient(
    circle,
    rgb(26 208 92 / 0.62) 0%,
    rgb(26 208 92 / 0.24) 36%,
    transparent 72%
  );
  filter: blur(24px);
  opacity: 0.55;
  transform: scale(1);
  animation: cover-glow-pulse 1.16s ease-in-out infinite;
}

.player-cover-frame {
  @apply relative flex items-center justify-center overflow-hidden rounded-2xl bg-primary/10 sm:rounded-3xl;
  z-index: 1;
  width: min(18rem, 58vw);
  height: min(18rem, 58vw);
  aspect-ratio: 1 / 1;
}

@keyframes cover-glow-pulse {
  0%,
  100% {
    opacity: 0.42;
    filter: blur(18px);
    transform: scale(0.96);
  }
  42% {
    opacity: 0.9;
    filter: blur(30px);
    transform: scale(1.18);
  }
}

@media (prefers-reduced-motion: reduce) {
  .player-cover-active::before {
    animation: none;
  }
}

.player-shell > section,
.player-now {
  overflow-x: hidden;
}

.similar-artists-card {
  @apply shrink-0 rounded-xl;
}

.lyrics-preview {
  box-shadow: inset 0 1px 0 rgb(255 255 255 / 0.04);
}

.lyrics-scroll {
  max-height: clamp(7.5rem, 22dvh, 13rem);
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  contain: layout paint;
  overscroll-behavior-y: contain;
  scrollbar-width: none;
}

.lyrics-scroll::-webkit-scrollbar {
  display: none;
}

.lyrics-line {
  @apply py-1.5 text-center text-sm font-medium leading-snug text-base-content/40 transition-all duration-200 sm:text-base;
}

.lyrics-line-active {
  @apply text-primary;
  transform: scale(1.04);
  text-shadow: 0 0 18px rgb(var(--color-primary) / 0.24);
}

.lyrics-offset-controls {
  @apply flex h-7 items-center overflow-hidden rounded-full border border-white/10 bg-base-100/60 text-xs text-base-content/55;
}

.lyrics-offset-btn,
.lyrics-offset-value {
  @apply flex h-full items-center justify-center transition-colors hover:bg-primary/10 hover:text-primary focus-visible:bg-primary/10 focus-visible:text-primary focus-visible:outline-none;
}

.lyrics-offset-btn {
  @apply w-7;
}

.lyrics-offset-value {
  @apply min-w-12 px-2 font-medium tabular-nums;
}

.lyrics-plain {
  @apply max-h-40 overflow-y-auto whitespace-pre-line text-center text-sm leading-relaxed text-base-content/60;
  -webkit-overflow-scrolling: touch;
}

.player-queue {
  @apply rounded-2xl border border-white/10 bg-base-100/45 p-3;
  min-height: 10rem;
  box-shadow: inset 0 1px 0 rgb(255 255 255 / 0.04);
}

.player-queue-list {
  @apply grid gap-2;
  grid-template-columns: repeat(auto-fit, minmax(13rem, 1fr));
}

.player-queue-item {
  @apply flex min-w-0 items-center gap-2 rounded-xl border border-white/10 bg-white/5 p-2 text-left transition-colors hover:bg-white/10 focus-visible:bg-white/10 focus-visible:outline-none;
}

.player-queue-cover {
  @apply relative h-11 w-11 shrink-0 overflow-hidden rounded-lg bg-primary/10;
}

@media (max-width: 1023px) {
  .player-view {
    height: calc(
      100dvh - var(--app-header-height) - var(--app-safe-top) -
        var(--app-bottom-nav-height) - var(--app-safe-bottom)
    );
    max-height: calc(
      100dvh - var(--app-header-height) - var(--app-safe-top) -
        var(--app-bottom-nav-height) - var(--app-safe-bottom)
    );
    overflow: hidden;
  }

  .player-page {
    min-height: 0;
    min-width: 0;
  }

  .player-content {
    overflow-x: hidden;
    overflow-y: auto;
    -webkit-overflow-scrolling: touch;
    overscroll-behavior-y: auto;
    scrollbar-width: none;
    touch-action: pan-y;
  }

  .player-content::-webkit-scrollbar {
    display: none;
  }

  .player-shell {
    display: contents;
    min-height: 0;
  }

  .player-shell > section {
    order: 1;
  }

  .similar-artists-card {
    order: 2;
  }

  .player-shell > aside {
    order: 3;
  }

  .player-shell > .panel-glow-shell-grow {
    flex: 0 0 auto;
    max-height: min(32rem, 55dvh);
    min-height: 0;
  }

  .player-now {
    flex-shrink: 0;
  }

  .player-cover {
    width: auto;
    height: auto;
    aspect-ratio: 1 / 1;
  }

  .player-cover-frame {
    width: min(28vw, 6.5rem);
    height: min(28vw, 6.5rem);
  }

  .player-queue-list {
    grid-template-columns: minmax(0, 1fr);
  }

  .player-play-btn {
    height: 3rem;
    width: 3rem;
  }

  .player-details {
    display: flex;
    flex: 1 1 auto;
    flex-direction: column;
    min-height: 0;
    overflow-x: hidden;
    overflow-y: auto;
    -webkit-overflow-scrolling: touch;
    overscroll-behavior-y: auto;
    scrollbar-width: none;
    touch-action: pan-y;
  }

  .player-details::-webkit-scrollbar {
    display: none;
  }
}

@media (min-width: 1024px) {
  .player-page {
    --player-panel-height: clamp(42rem, calc(100dvh - 7rem), 56rem);
  }

  .player-view {
    height: auto;
    max-height: none;
    overflow: visible;
  }

  .player-content {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 360px;
    gap: 1.5rem;
  }

  .player-shell {
    display: contents;
  }

  .player-shell > section {
    grid-column: 1;
    align-self: start;
    height: var(--player-panel-height);
    min-width: 0;
    overflow: hidden;
  }

  .player-shell > aside {
    grid-column: 2;
    align-self: start;
    display: flex;
    height: var(--player-panel-height);
    min-width: 0;
    overflow: hidden;
  }

  .similar-artists-card {
    grid-column: 1 / -1;
    min-width: 0;
  }

  .player-details {
    flex: 1 1 auto;
    height: 100%;
    overflow-y: auto;
  }

  .player-cover {
    width: auto;
    height: auto;
    aspect-ratio: 1 / 1;
  }

  .player-cover-frame {
    width: 16rem;
    height: 16rem;
  }

  .player-queue {
    max-height: 20rem;
    min-height: 12rem;
    overflow-y: auto;
    scrollbar-width: none;
  }

  .player-queue::-webkit-scrollbar {
    display: none;
  }

  .player-play-btn {
    height: 3.5rem;
    width: 3.5rem;
  }
}

.player-progress {
  position: relative;
  width: 100%;
  padding: 0.875rem 0;
  cursor: pointer;
  touch-action: none;
  user-select: none;
  -webkit-tap-highlight-color: transparent;
  outline: none;
}

.player-progress:focus-visible .player-progress-track {
  box-shadow: 0 0 0 2px rgba(26, 208, 92, 0.35);
}

.player-progress-track {
  position: relative;
  height: 4px;
  border-radius: 9999px;
  background: rgba(255, 255, 255, 0.1);
  transition: height 160ms ease;
}

[data-theme='downtify-light'] .player-progress-track {
  background: rgba(0, 0, 0, 0.1);
}

.player-progress:hover .player-progress-track,
.player-progress--scrubbing .player-progress-track {
  height: 6px;
}

.player-progress-fill {
  position: absolute;
  inset: 0 auto 0 0;
  border-radius: 9999px;
  background: #1ad05c;
  transition: width 100ms linear;
  will-change: width;
}

.player-progress-thumb {
  position: absolute;
  top: 50%;
  left: 0;
  height: 14px;
  width: 14px;
  border-radius: 9999px;
  background: #1ad05c;
  box-shadow: 0 0 12px rgba(26, 208, 92, 0.45);
  transform: translate(-50%, -50%) scale(0.9);
  opacity: 0;
  transition:
    left 100ms linear,
    opacity 160ms ease,
    transform 160ms ease,
    width 160ms ease,
    height 160ms ease;
  will-change: left, transform;
}

.player-progress:hover .player-progress-thumb,
.player-progress--scrubbing .player-progress-thumb,
.player-progress:focus-visible .player-progress-thumb {
  opacity: 1;
  transform: translate(-50%, -50%) scale(1);
}

.player-progress--scrubbing .player-progress-fill,
.player-progress--scrubbing .player-progress-thumb {
  transition: none;
}

@media (hover: none), (pointer: coarse) {
  .player-progress {
    padding: 1rem 0;
  }

  .player-progress-track {
    height: 5px;
  }

  .player-progress-thumb {
    opacity: 1;
    height: 18px;
    width: 18px;
    transform: translate(-50%, -50%) scale(1);
  }

  .player-progress--scrubbing .player-progress-thumb {
    height: 20px;
    width: 20px;
  }
}

.player-range {
  -webkit-appearance: none;
  appearance: none;
  background: rgba(255, 255, 255, 0.1);
  height: 4px;
  border-radius: 9999px;
  outline: none;
}
[data-theme='downtify-light'] .player-range {
  background: rgba(0, 0, 0, 0.1);
}
.player-range::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  height: 14px;
  width: 14px;
  border-radius: 9999px;
  background: #1ad05c;
  cursor: pointer;
  box-shadow: 0 0 12px rgba(26, 208, 92, 0.45);
}
.player-range::-moz-range-thumb {
  height: 14px;
  width: 14px;
  border-radius: 9999px;
  background: #1ad05c;
  border: none;
  cursor: pointer;
  box-shadow: 0 0 12px rgba(26, 208, 92, 0.45);
}
.pulse-glow {
  animation: glow 2.4s ease-in-out infinite;
}
@keyframes glow {
  0%,
  100% {
    box-shadow: 0 0 36px rgba(26, 208, 92, 0.3);
  }
  50% {
    box-shadow: 0 0 60px rgba(26, 208, 92, 0.55);
  }
}

@keyframes download-press {
  0% {
    transform: scale(1);
  }
  55% {
    transform: scale(0.9);
  }
  100% {
    transform: scale(1);
  }
}

@keyframes download-spin {
  to {
    transform: rotate(360deg);
  }
}

@keyframes download-pulse {
  0%,
  100% {
    box-shadow:
      0 0 0 1px rgb(26 208 92 / 0.16),
      0 0 0 rgb(26 208 92 / 0);
  }
  50% {
    box-shadow:
      0 0 0 1px rgb(26 208 92 / 0.34),
      0 0 18px rgb(26 208 92 / 0.32);
  }
}

@keyframes download-pop {
  0% {
    transform: scale(0.92);
  }
  55% {
    transform: scale(1.08);
  }
  100% {
    transform: scale(1);
  }
}

.player-detail-heading {
  @apply text-xs font-semibold uppercase tracking-wide text-base-content/45;
}

.player-details {
  scrollbar-width: none;
  overscroll-behavior-y: auto;
}

.player-details::-webkit-scrollbar {
  display: none;
}

.player-detail-card {
  @apply flex flex-col gap-3 rounded-2xl border border-white/10 bg-white/5 p-3 sm:gap-4 sm:p-4;
}

.player-detail-card-active {
  @apply border-primary/30 bg-primary/10;
}

.player-detail-main {
  @apply flex min-w-0 items-start gap-3;
}

.player-detail-actions {
  @apply flex w-full flex-wrap items-start justify-end gap-2;
}

.player-artist-actions {
  @apply flex-nowrap items-center justify-start;
}

.player-artist-actions :deep(.library-artist-monitor) {
  @apply flex-row items-center;
}

.player-detail-cover {
  @apply relative h-16 w-16 shrink-0 overflow-hidden rounded-xl bg-primary/10;
}

.player-detail-title {
  @apply truncate text-base font-semibold leading-snug;
}

.player-detail-meta {
  @apply mt-0.5 text-xs text-base-content/50;
}

.player-detail-empty {
  @apply rounded-lg border border-white/10 bg-white/5 px-3 py-4 text-center text-xs text-base-content/45;
}

.similar-artists-grid {
  @apply flex gap-2 overflow-x-auto pb-1;
  cursor: grab;
  user-select: none;
  scrollbar-width: none;
  -ms-overflow-style: none;
  -webkit-overflow-scrolling: touch;
}

.similar-artists-grid.is-dragging {
  cursor: grabbing;
  scroll-behavior: auto;
}

.similar-artists-grid::-webkit-scrollbar {
  display: none;
  width: 0;
  height: 0;
}

.similar-artist-item {
  @apply w-[4.5rem] min-w-[4.5rem] cursor-pointer text-center outline-none transition-transform hover:-translate-y-0.5 focus-visible:-translate-y-0.5;
}

.similar-track-item {
  @apply w-[10rem] min-w-[10rem] cursor-pointer rounded-lg p-1 text-left outline-none transition-colors hover:bg-white/5 focus-visible:bg-white/5;
}

.similar-track-download {
  @apply flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-primary transition-colors hover:bg-primary/10 focus-visible:bg-primary/10 focus-visible:outline-none;
}

.download-button-loading {
  @apply pointer-events-none;
  animation:
    download-press 220ms ease-out,
    download-pulse 1.1s ease-in-out infinite;
}

.download-button-loading svg {
  animation: download-spin 900ms linear infinite;
}

.download-button-done {
  animation: download-pop 420ms cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow:
    0 0 0 1px rgb(26 208 92 / 0.26),
    0 0 22px rgb(26 208 92 / 0.32);
}

.similar-track-owned {
  @apply flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary;
}

.similar-owned-badge {
  @apply absolute bottom-1 right-1 flex h-6 w-6 items-center justify-center rounded-full border border-primary/30 bg-base-100/90 text-primary shadow;
}

.similar-artist-cover {
  @apply relative mx-auto aspect-square w-full max-w-[4.5rem] overflow-hidden rounded-lg bg-primary/10;
}

.similar-artist-name {
  @apply mt-1.5 line-clamp-1 text-xs font-medium leading-tight text-base-content/70;
}

.similar-artists-card {
  width: 100%;
  min-width: 0;
  align-self: stretch;
}

.artist-modal-backdrop {
  @apply fixed inset-0 z-[70] flex items-end justify-center bg-black/70 sm:items-center sm:p-5;
}

.artist-modal {
  @apply flex max-h-[92dvh] w-full max-w-2xl flex-col overflow-hidden rounded-t-2xl border border-white/10 shadow-2xl sm:rounded-2xl;
}

.artist-modal-header {
  @apply flex shrink-0 items-center justify-between gap-3 border-b border-white/10 px-4 py-3 sm:px-5;
}

.artist-modal-avatar {
  @apply relative flex h-14 w-14 shrink-0 items-center justify-center overflow-hidden rounded-lg bg-primary/10;
}

.artist-modal-toolbar {
  @apply flex shrink-0 flex-wrap items-center justify-between gap-3 border-b border-white/10 px-4 py-3 sm:px-5;
}

.artist-modal-results {
  @apply min-h-0 flex-1 overflow-y-auto p-3 sm:p-4;
  -webkit-overflow-scrolling: touch;
}

.artist-result {
  @apply flex min-w-0 items-center gap-3 rounded-lg border border-white/10 bg-base-100/50 p-2.5;
}

.queue-album-card {
  @apply w-full min-w-0 max-w-full overflow-hidden rounded-lg border border-white/10 bg-base-100/35;
}

.queue-album-main {
  @apply grid min-w-0 gap-3 p-2.5;
}

.queue-album-summary {
  @apply flex w-full min-w-0 items-center gap-3;
}

.queue-album-footer {
  @apply grid w-full min-w-0 gap-2;
}

.queue-album-status {
  @apply min-w-0 text-xs leading-snug;
}

.queue-album-actions {
  @apply grid w-full min-w-0 grid-cols-2 gap-2;
}

.queue-album-action-btn {
  @apply inline-flex h-8 min-w-0 max-w-full items-center justify-center gap-1.5 overflow-hidden rounded-full border border-white/10 bg-base-100/70 px-2.5 text-xs font-semibold whitespace-nowrap transition-colors hover:bg-base-100/90 disabled:opacity-50 sm:px-3;
}

.queue-album-action-btn svg {
  @apply shrink-0;
}

.queue-album-download-btn {
  @apply text-primary;
}

.queue-album-tracks {
  @apply border-t border-white/10 bg-black/10 p-2.5;
}

.queue-album-track {
  @apply flex min-w-0 items-center gap-2 rounded-lg bg-white/5 px-2.5 py-2;
}

.queue-album-track-summary {
  @apply mb-2 flex flex-wrap items-center justify-between gap-2 rounded-lg bg-base-100/45 px-2.5 py-2 text-xs font-medium text-base-content/55;
}

.queue-track-owned {
  @apply inline-flex shrink-0 items-center gap-1 rounded-full bg-primary/10 px-2 py-1 text-xs font-semibold text-primary;
}

.queue-track-download {
  @apply inline-flex shrink-0 items-center gap-1 rounded-full border border-amber-300/25 bg-amber-300/10 px-2 py-1 text-xs font-semibold text-amber-200 transition-colors hover:bg-amber-300/15 focus-visible:outline-none;
}

.artist-result-cover {
  @apply relative flex h-12 w-12 shrink-0 items-center justify-center overflow-hidden rounded-md bg-primary/10;
}

.track-modal {
  @apply flex max-h-[92dvh] w-[calc(100vw-0.75rem)] max-w-2xl flex-col overflow-hidden rounded-t-2xl border border-white/10 shadow-2xl sm:w-full sm:rounded-2xl;
}

.track-modal-body {
  @apply flex min-h-0 flex-1 flex-col gap-5 overflow-x-hidden overflow-y-auto p-3 sm:p-5;
  -webkit-overflow-scrolling: touch;
  -ms-overflow-style: none;
  overscroll-behavior-y: contain;
  scrollbar-width: none;
}

.track-modal-body::-webkit-scrollbar {
  width: 0;
  height: 0;
  display: none;
}

.track-modal-summary {
  @apply flex w-full min-w-0 flex-col items-start gap-5 sm:flex-row;
}

.track-modal-albums {
  @apply w-full min-w-0 max-w-full self-stretch overflow-x-hidden;
}

.track-modal-current-album {
  @apply flex w-full min-w-0 max-w-full items-center justify-between gap-3 rounded-lg border border-white/10 bg-white/5 p-2.5;
}

@media (max-width: 480px) {
  .queue-album-actions {
    grid-template-columns: minmax(0, 1fr);
  }
}

.track-modal-cover {
  @apply relative mx-auto aspect-square w-full max-w-56 shrink-0 overflow-hidden rounded-xl bg-primary/10 sm:mx-0 sm:h-52 sm:w-52 sm:max-w-none;
}

.track-modal-metadata {
  @apply mt-5 space-y-2 text-sm;
}

.track-modal-metadata > div {
  @apply grid grid-cols-[6rem_1fr] gap-3;
}

.track-modal-metadata dt {
  @apply text-base-content/45;
}

.track-modal-metadata dd {
  @apply min-w-0 truncate text-base-content/75;
}

.player-detail-card :deep(.library-artist-monitor) {
  @apply min-w-0 shrink-0;
}

.player-detail-card :deep(.library-artist-monitor .btn) {
  @apply h-9 whitespace-nowrap;
}

.player-detail-card :deep(.library-artist-monitor .monitor-alert) {
  @apply max-w-[16rem];
}
</style>
