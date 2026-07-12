<template>
  <div class="min-h-0 overflow-x-hidden">
    <Navbar />

    <main
      class="metadata-page mx-auto max-w-5xl overflow-x-hidden px-3 py-4 sm:px-6 sm:py-8"
    >
      <div class="mb-4 sm:mb-5 mobile-page-header">
        <div>
          <h1 class="text-2xl font-bold tracking-tight">
            {{ t('metadata.title') }}
          </h1>
          <p class="mt-1 text-sm text-base-content/60">
            {{ t('metadata.subtitle') }}
          </p>
        </div>
      </div>

      <div
        class="metadata-tab-shell tab-glow-shell"
        :class="{ 'metadata-tool-tabs-mobile-menu': useMobileToolMenu }"
      >
        <button
          v-for="tab in metadataToolTabs"
          :key="tab.id"
          class="metadata-tab-btn"
          :class="
            activeToolTab === tab.id
              ? 'bg-primary text-primary-content shadow-glow-sm'
              : 'text-base-content/60 hover:text-base-content'
          "
          @click="selectToolTab(tab.id)"
        >
          <Icon :icon="tab.icon" class="mr-2 inline h-4 w-4" />
          {{ tab.label }}
        </button>
      </div>

      <div
        v-if="useMobileToolMenu && metadataToolMenuOpen"
        class="metadata-mobile-menu-backdrop lg:hidden"
        @click="metadataToolMenuOpen = false"
      >
        <div class="metadata-mobile-menu surface" @click.stop>
          <button
            v-for="tab in metadataToolTabs"
            :key="tab.id"
            type="button"
            class="metadata-mobile-menu-item"
            :class="{
              'metadata-mobile-menu-item-active': activeToolTab === tab.id,
            }"
            @click="selectToolTab(tab.id)"
          >
            <Icon :icon="tab.icon" class="h-5 w-5 shrink-0" />
            <span class="min-w-0 truncate">{{ tab.label }}</span>
          </button>
        </div>
      </div>

      <section v-if="activeToolTab === 'metadata'" class="metadata-section">
        <div class="metadata-header">
          <div class="metadata-toolbar">
            <select
              v-model.number="scanLimit"
              class="metadata-select"
              :disabled="loading"
              :title="t('metadata.resultLimit')"
            >
              <option :value="25">25</option>
              <option :value="50">50</option>
              <option :value="100">100</option>
            </select>
            <button
              class="btn btn-primary btn-sm metadata-btn px-5"
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
            <button
              class="btn btn-sm metadata-btn border-white/10 bg-base-100/85 hover:bg-base-100"
              :disabled="loading"
              @click="scanAll"
            >
              <Icon icon="clarity:fast-forward-line" class="h-4 w-4 mr-2" />
              {{ t('metadata.scanAll') }}
            </button>
            <button
              class="btn btn-sm metadata-btn border-white/10 bg-base-100/85 hover:bg-base-100"
              :disabled="
                loading ||
                activeTab !== 'needs' ||
                items.length === 0 ||
                repairingAll
              "
              @click="repairAll"
            >
              <span
                v-if="repairingAll"
                class="loading loading-spinner loading-xs mr-2"
              />
              <Icon
                v-else
                icon="clarity:check-circle-line"
                class="h-4 w-4 mr-2"
              />
              {{ t('metadata.repairAll') }}
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

        <section class="metadata-stat-grid">
          <div class="metadata-stat-card surface rounded-2xl">
            <p class="metadata-stat-label">
              {{ t('metadata.scanned') }}
            </p>
            <p class="metadata-stat-value">{{ summary.scanned }}</p>
          </div>
          <div class="metadata-stat-card surface rounded-2xl">
            <p class="metadata-stat-label">
              {{ t('metadata.needsFix') }}
            </p>
            <p class="metadata-stat-value text-primary">
              {{ summary.matched }}
            </p>
          </div>
          <div class="metadata-stat-card surface rounded-2xl">
            <p class="metadata-stat-label">
              {{ t('metadata.total') }}
            </p>
            <p class="metadata-stat-value">{{ summary.total }}</p>
          </div>
        </section>

        <p class="mb-5 text-xs text-base-content/45">
          {{ t('metadata.serverOnly') }}
        </p>

        <div class="metadata-tab-shell tab-glow-shell">
          <button
            class="metadata-tab-btn"
            :class="
              activeTab === 'needs'
                ? 'bg-primary text-primary-content shadow-glow-sm'
                : 'text-base-content/60 hover:text-base-content'
            "
            @click="activeTab = 'needs'"
          >
            {{ t('metadata.needsFix') }}
            <span
              class="ml-2 rounded-full bg-current/10 px-2 py-0.5 text-sm font-bold"
            >
              {{ items.length }}
            </span>
          </button>
          <button
            class="metadata-tab-btn"
            :class="
              activeTab === 'completed'
                ? 'bg-primary text-primary-content shadow-glow-sm'
                : 'text-base-content/60 hover:text-base-content'
            "
            @click="activeTab = 'completed'"
          >
            {{ t('metadata.completed') }}
            <span
              class="ml-2 rounded-full bg-current/10 px-2 py-0.5 text-sm font-bold"
            >
              {{ completedItems.length }}
            </span>
          </button>
          <button
            class="metadata-tab-btn"
            :class="
              activeTab === 'clean'
                ? 'bg-primary text-primary-content shadow-glow-sm'
                : 'text-base-content/60 hover:text-base-content'
            "
            @click="activeTab = 'clean'"
          >
            <span class="sm:hidden">{{ t('metadata.cleanShort') }}</span>
            <span class="hidden sm:inline">{{ t('metadata.clean') }}</span>
            <span
              class="ml-2 rounded-full bg-current/10 px-2 py-0.5 text-sm font-bold"
            >
              {{ cleanItems.length }}
            </span>
          </button>
        </div>

        <div
          class="max-h-[45rem] overflow-x-hidden overflow-y-auto pr-1 sm:pr-2"
        >
          <div
            v-if="loading && visibleItems.length === 0"
            class="metadata-artist-grid"
          >
            <div
              v-for="n in 8"
              :key="n"
              class="overflow-hidden rounded-2xl border border-white/10 bg-base-100/60"
            >
              <div class="skeleton scan-skeleton-glow aspect-square w-full" />
              <div class="space-y-2 p-3">
                <div class="skeleton h-4 w-2/3 rounded-full" />
                <div class="skeleton h-3 w-full rounded-full" />
              </div>
            </div>
          </div>

          <div
            v-else-if="visibleItems.length === 0"
            class="surface rounded-2xl p-10 text-center"
          >
            <Icon
              icon="clarity:tag-line"
              class="mx-auto mb-3 h-10 w-10 text-base-content/20"
            />
            <p class="text-sm text-base-content/50">
              {{ loading ? t('metadata.scanning') : t('metadata.empty') }}
            </p>
          </div>

          <div v-else class="metadata-artist-grid">
            <article
              v-for="item in visibleItems"
              :key="item.file"
              class="overflow-hidden rounded-2xl border border-primary/20 bg-base-100/75 shadow-glow-sm"
              :class="
                applying[item.file]
                  ? 'border-primary/40 ring-2 ring-primary/30'
                  : ''
              "
            >
              <div class="relative aspect-square bg-base-100/80">
                <img
                  v-if="metadataCoverUrl(item)"
                  :src="metadataCoverUrl(item)"
                  :alt="displaySong(item.current)"
                  class="h-full w-full object-cover"
                  loading="lazy"
                  @error="markMetadataCoverFailed(item.file)"
                />
                <div
                  v-else
                  class="flex h-full w-full items-center justify-center text-base-content/25"
                >
                  <Icon icon="clarity:music-note-line" class="h-12 w-12" />
                </div>
                <span
                  class="pill absolute left-2 top-2 max-w-[calc(100%-1rem)] truncate text-[0.65rem]"
                  :class="metadataStatusBadgeClass()"
                >
                  {{ metadataStatusBadge() }}
                </span>
              </div>
              <div class="space-y-2 p-3">
                <p class="line-clamp-2 text-sm font-semibold leading-snug">
                  {{ displaySong(item.current) }}
                </p>
                <p class="truncate text-xs text-base-content/45">
                  {{ item.file }}
                </p>
                <p class="line-clamp-2 text-xs text-primary">
                  {{ displaySong(item.candidate) }}
                </p>
                <div
                  v-if="item.changes.length"
                  class="space-y-1 rounded-xl border border-white/10 bg-base-100/70 p-2"
                >
                  <div
                    v-for="change in item.changes.slice(0, 2)"
                    :key="`${item.file}-${change.field}`"
                    class="text-[0.7rem] leading-snug"
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
                  <p
                    v-if="item.changes.length > 2"
                    class="text-[0.65rem] text-base-content/45"
                  >
                    +{{ item.changes.length - 2 }}
                    {{ t('metadata.moreChanges') }}
                  </p>
                </div>
                <p v-else class="text-xs text-base-content/45">
                  {{ t('metadata.idsOnly') }}
                </p>
                <button
                  v-if="activeTab === 'needs'"
                  type="button"
                  class="btn btn-sm metadata-card-btn w-full border-white/10 bg-base-100/85 hover:bg-base-100"
                  :class="fixed[item.file] ? 'text-primary' : ''"
                  :disabled="applying[item.file] || fixed[item.file]"
                  @click="apply(item)"
                >
                  <span
                    v-if="applying[item.file]"
                    class="loading loading-spinner loading-xs mr-2"
                  />
                  <Icon v-else icon="clarity:check-line" class="mr-2 h-4 w-4" />
                  {{
                    applying[item.file]
                      ? t('metadata.fixing')
                      : fixed[item.file]
                      ? t('metadata.fixed')
                      : t('metadata.apply')
                  }}
                </button>
              </div>
            </article>
          </div>
        </div>
      </section>

      <section v-if="activeToolTab === 'album-images'" class="metadata-section">
        <div class="metadata-header">
          <div class="metadata-toolbar">
            <select
              v-model.number="albumImageLimit"
              class="metadata-select"
              :disabled="albumImageLoading"
              :title="t('metadata.albumImageLimit')"
            >
              <option :value="25">25</option>
              <option :value="50">50</option>
              <option :value="100">100</option>
            </select>
            <button
              class="btn btn-primary btn-sm metadata-btn px-5"
              :disabled="albumImageLoading"
              @click="scanAlbumImages"
            >
              <span
                v-if="albumImageLoading"
                class="loading loading-spinner loading-xs mr-2"
              />
              <Icon v-else icon="clarity:image-line" class="h-4 w-4 mr-2" />
              {{ t('metadata.scanAlbumImages') }}
            </button>
            <button
              class="btn btn-sm metadata-btn border-white/10 bg-base-100/85 hover:bg-base-100"
              :disabled="albumImageLoading"
              @click="scanAllAlbumImages"
            >
              <Icon icon="clarity:fast-forward-line" class="h-4 w-4 mr-2" />
              {{ t('metadata.scanAll') }}
            </button>
            <button
              class="btn btn-sm metadata-btn border-white/10 bg-base-100/85 hover:bg-base-100"
              :disabled="
                albumImageLoading ||
                albumImageItems.length === 0 ||
                repairingAllAlbumImages
              "
              @click="repairAllAlbumImages"
            >
              <span
                v-if="repairingAllAlbumImages"
                class="loading loading-spinner loading-xs mr-2"
              />
              <Icon
                v-else
                icon="clarity:check-circle-line"
                class="h-4 w-4 mr-2"
              />
              {{ t('metadata.fixAllAlbumImages') }}
            </button>
          </div>
        </div>

        <div
          v-if="albumImageError"
          class="surface mb-4 flex items-start gap-3 rounded-2xl p-4 text-sm"
          :class="
            repairingAllAlbumImages ? 'text-base-content/60' : 'text-error'
          "
        >
          <Icon
            icon="clarity:exclamation-circle-line"
            class="h-5 w-5 shrink-0"
          />
          <span class="min-w-0 break-words">{{ albumImageError }}</span>
        </div>

        <section class="metadata-stat-grid-4">
          <div class="metadata-stat-card surface rounded-2xl">
            <p class="metadata-stat-label">
              {{ t('metadata.scannedAlbums') }}
            </p>
            <p class="metadata-stat-value">
              {{ albumImageSummary.scannedAlbums }}
            </p>
          </div>
          <div class="metadata-stat-card surface rounded-2xl">
            <p class="metadata-stat-label">
              {{ t('metadata.scannedTracks') }}
            </p>
            <p class="metadata-stat-value">
              {{ albumImageSummary.scannedTracks }}
            </p>
          </div>
          <div class="metadata-stat-card surface rounded-2xl">
            <p class="metadata-stat-label">{{ t('metadata.needsFix') }}</p>
            <p class="metadata-stat-value text-primary">
              {{ albumImageItems.length }}
            </p>
          </div>
          <div class="metadata-stat-card surface rounded-2xl">
            <p class="metadata-stat-label">{{ t('metadata.completed') }}</p>
            <p class="metadata-stat-value">
              {{ completedAlbumImages.length }}
            </p>
          </div>
        </section>

        <div class="metadata-tab-shell tab-glow-shell">
          <button
            class="metadata-tab-btn"
            :class="
              activeAlbumImageTab === 'needs'
                ? 'bg-primary text-primary-content shadow-glow-sm'
                : 'text-base-content/60 hover:text-base-content'
            "
            @click="activeAlbumImageTab = 'needs'"
          >
            {{ t('metadata.needsFix') }}
            <span class="metadata-tab-badge">{{ albumImageItems.length }}</span>
          </button>
          <button
            class="metadata-tab-btn"
            :class="
              activeAlbumImageTab === 'completed'
                ? 'bg-primary text-primary-content shadow-glow-sm'
                : 'text-base-content/60 hover:text-base-content'
            "
            @click="activeAlbumImageTab = 'completed'"
          >
            {{ t('metadata.completed') }}
            <span class="metadata-tab-badge">
              {{ completedAlbumImages.length }}
            </span>
          </button>
          <button
            class="metadata-tab-btn"
            :class="
              activeAlbumImageTab === 'clean'
                ? 'bg-primary text-primary-content shadow-glow-sm'
                : 'text-base-content/60 hover:text-base-content'
            "
            @click="activeAlbumImageTab = 'clean'"
          >
            <span class="sm:hidden">{{ t('metadata.cleanShort') }}</span>
            <span class="hidden sm:inline">{{ t('metadata.clean') }}</span>
            <span class="metadata-tab-badge">
              {{ cleanAlbumImageItems.length }}
            </span>
          </button>
        </div>

        <div
          class="metadata-album-artist-panel surface-strong mb-5 rounded-2xl p-3 sm:p-4"
        >
          <div class="mb-3">
            <label class="relative block">
              <Icon
                icon="clarity:search-line"
                class="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-base-content/40"
              />
              <input
                v-model.trim="albumImageArtistQuery"
                type="search"
                class="input-modern input-modern-plain h-11 w-full pl-10 pr-10 text-sm"
                :placeholder="t('metadata.searchAlbumImageArtists')"
              />
              <button
                v-if="albumImageArtistQuery"
                type="button"
                class="absolute right-2 top-1/2 flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-full text-base-content/45 transition hover:bg-white/10 hover:text-base-content"
                :title="t('metadata.clearSearch')"
                @click="albumImageArtistQuery = ''"
              >
                <Icon icon="clarity:times-line" class="h-4 w-4" />
              </button>
            </label>
          </div>

          <div class="metadata-album-artist-scroll">
            <div
              v-if="filteredAlbumImageArtists.length"
              class="metadata-artist-grid"
            >
              <button
                v-for="artist in filteredAlbumImageArtists"
                :key="artist.name"
                type="button"
                class="metadata-album-artist-card overflow-hidden rounded-2xl border border-primary/20 bg-base-100/90 text-left shadow-glow-sm transition hover:border-primary/40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40"
                @click="openAlbumArtistModal(artist)"
              >
                <div class="relative aspect-square bg-base-100">
                  <img
                    v-if="albumArtistCoverUrl(artist)"
                    :src="albumArtistCoverUrl(artist)"
                    :alt="artist.name"
                    class="h-full w-full object-cover"
                    loading="lazy"
                  />
                  <div
                    v-else
                    class="flex h-full w-full items-center justify-center text-base-content/25"
                  >
                    <Icon icon="clarity:user-line" class="h-12 w-12" />
                  </div>
                </div>
                <div class="space-y-1 p-3">
                  <p class="truncate text-sm font-semibold">
                    {{ artist.name }}
                  </p>
                  <p class="text-xs text-base-content/45">
                    {{
                      t('metadata.artistAlbumCount', {
                        count: albumImageAlbumsForArtist(artist).length,
                      })
                    }}
                  </p>
                </div>
              </button>
            </div>
            <div
              v-else-if="albumImageArtists.length"
              class="rounded-2xl border border-white/10 bg-base-100/90 p-8 text-center text-sm text-base-content/50"
            >
              <Icon
                icon="clarity:search-line"
                class="mx-auto mb-3 h-10 w-10 text-base-content/20"
              />
              <p>{{ t('metadata.emptyAlbumImageArtistSearch') }}</p>
            </div>
          </div>
          <div
            v-if="!albumImageArtists.length"
            class="surface rounded-2xl p-8 text-center text-sm text-base-content/50"
          >
            <Icon
              icon="clarity:image-line"
              class="mx-auto mb-3 h-10 w-10 text-base-content/20"
            />
            <p>
              {{
                hasAlbumImageScanData
                  ? emptyAlbumImageMessage
                  : t('metadata.albumImagesLibraryEmpty')
              }}
            </p>
          </div>
        </div>
      </section>

      <section v-if="activeToolTab === 'images'" class="metadata-section">
        <div class="metadata-header">
          <div class="metadata-toolbar">
            <select
              v-model.number="artistImageLimit"
              class="metadata-select"
              :disabled="artistImageLoading"
              :title="t('metadata.artistImageLimit')"
            >
              <option :value="25">25</option>
              <option :value="50">50</option>
              <option :value="100">100</option>
            </select>
            <button
              class="btn btn-primary btn-sm metadata-btn px-5"
              :disabled="artistImageLoading"
              @click="scanArtistImages"
            >
              <span
                v-if="artistImageLoading"
                class="loading loading-spinner loading-xs mr-2"
              />
              <Icon v-else icon="clarity:image-line" class="h-4 w-4 mr-2" />
              {{ t('metadata.scanArtistImages') }}
            </button>
            <button
              class="btn btn-sm metadata-btn border-white/10 bg-base-100/85 hover:bg-base-100"
              :disabled="artistImageLoading"
              @click="scanAllArtistImages"
            >
              <Icon icon="clarity:fast-forward-line" class="h-4 w-4 mr-2" />
              {{ t('metadata.scanAll') }}
            </button>
            <button
              class="btn btn-sm metadata-btn border-white/10 bg-base-100/85 hover:bg-base-100"
              :disabled="artistImageItems.length === 0 || repairingAllImages"
              @click="repairAllArtistImages"
            >
              <span
                v-if="repairingAllImages"
                class="loading loading-spinner loading-xs mr-2"
              />
              <Icon
                v-else
                icon="clarity:check-circle-line"
                class="h-4 w-4 mr-2"
              />
              {{ t('metadata.fixAllArtistImages') }}
            </button>
          </div>
        </div>

        <div
          v-if="artistImageError"
          class="surface mb-4 flex items-start gap-3 rounded-2xl p-4 text-sm text-error"
        >
          <Icon
            icon="clarity:exclamation-circle-line"
            class="h-5 w-5 shrink-0"
          />
          <span class="min-w-0 break-words">{{ artistImageError }}</span>
        </div>

        <section class="metadata-stat-grid">
          <div class="metadata-stat-card surface rounded-2xl">
            <p class="metadata-stat-label">
              {{ t('metadata.scanned') }}
            </p>
            <p class="metadata-stat-value">
              {{ artistImageSummary.scanned }}
            </p>
          </div>
          <div class="metadata-stat-card surface rounded-2xl">
            <p class="metadata-stat-label">
              {{ t('metadata.missingImages') }}
            </p>
            <p class="metadata-stat-value text-primary">
              {{ artistImageItems.length }}
            </p>
          </div>
          <div class="metadata-stat-card surface rounded-2xl">
            <p class="metadata-stat-label">
              {{ t('metadata.completed') }}
            </p>
            <p class="metadata-stat-value">
              {{ completedArtistImages.length }}
            </p>
          </div>
        </section>

        <div class="metadata-tab-shell tab-glow-shell">
          <button
            class="metadata-tab-btn"
            :class="
              activeArtistImageTab === 'needs'
                ? 'bg-primary text-primary-content shadow-glow-sm'
                : 'text-base-content/60 hover:text-base-content'
            "
            @click="activeArtistImageTab = 'needs'"
          >
            {{ t('metadata.needsFix') }}
            <span class="metadata-tab-badge">
              {{ artistImageItems.length }}
            </span>
          </button>
          <button
            class="metadata-tab-btn"
            :class="
              activeArtistImageTab === 'completed'
                ? 'bg-primary text-primary-content shadow-glow-sm'
                : 'text-base-content/60 hover:text-base-content'
            "
            @click="activeArtistImageTab = 'completed'"
          >
            {{ t('metadata.completed') }}
            <span class="metadata-tab-badge">
              {{ completedArtistImages.length }}
            </span>
          </button>
          <button
            class="metadata-tab-btn"
            :class="
              activeArtistImageTab === 'clean'
                ? 'bg-primary text-primary-content shadow-glow-sm'
                : 'text-base-content/60 hover:text-base-content'
            "
            @click="activeArtistImageTab = 'clean'"
          >
            <span class="sm:hidden">{{ t('metadata.cleanShort') }}</span>
            <span class="hidden sm:inline">{{ t('metadata.clean') }}</span>
            <span class="metadata-tab-badge">
              {{ cleanArtistImageItems.length }}
            </span>
          </button>
          <button
            class="metadata-tab-btn"
            :class="
              activeArtistImageTab === 'failed'
                ? 'bg-primary text-primary-content shadow-glow-sm'
                : 'text-base-content/60 hover:text-base-content'
            "
            @click="activeArtistImageTab = 'failed'"
          >
            <span class="sm:hidden">{{ t('metadata.repairFailedShort') }}</span>
            <span class="hidden sm:inline">{{
              t('metadata.repairFailed')
            }}</span>
            <span class="metadata-tab-badge">
              {{ failedArtistImages.length }}
            </span>
          </button>
        </div>

        <div
          class="max-h-[34rem] overflow-x-hidden overflow-y-auto pr-1 sm:pr-2"
        >
          <div
            v-if="artistImageLoading && visibleArtistImageItems.length === 0"
            class="metadata-artist-grid"
          >
            <div
              v-for="n in 8"
              :key="n"
              class="overflow-hidden rounded-2xl border border-white/10 bg-base-100/60"
            >
              <div class="skeleton scan-skeleton-glow aspect-square w-full" />
              <div class="space-y-2 p-3">
                <div class="skeleton h-4 w-2/3 rounded-full" />
                <div class="skeleton h-3 w-full rounded-full" />
              </div>
            </div>
          </div>

          <div
            v-else-if="visibleArtistImageItems.length === 0"
            class="surface rounded-2xl p-10 text-center"
          >
            <Icon
              icon="clarity:image-line"
              class="mx-auto mb-3 h-10 w-10 text-base-content/20"
            />
            <p class="text-sm text-base-content/50">
              {{
                artistImageLoading
                  ? t('metadata.scanning')
                  : emptyArtistImageMessage
              }}
            </p>
          </div>

          <div v-else class="metadata-artist-grid">
            <article
              v-for="item in visibleArtistImageItems"
              :key="itemKey(item)"
              class="overflow-hidden rounded-2xl border border-primary/20 bg-base-100/75 shadow-glow-sm"
              :class="
                applyingArtistImages[itemKey(item)]
                  ? 'border-primary/40 ring-2 ring-primary/30'
                  : ''
              "
            >
              <div class="relative aspect-square bg-base-100/80">
                <img
                  v-if="artistImagePreviewUrl(item)"
                  :src="artistImagePreviewUrl(item)"
                  :alt="artistImageItemArtist(item)"
                  class="h-full w-full object-cover"
                  loading="lazy"
                />
                <div
                  v-else
                  class="flex h-full w-full flex-col items-center justify-center gap-2 text-base-content/30"
                >
                  <Icon
                    :icon="
                      activeArtistImageTab === 'needs'
                        ? 'clarity:user-line'
                        : 'clarity:image-line'
                    "
                    class="h-12 w-12"
                  />
                  <span
                    v-if="activeArtistImageTab === 'needs'"
                    class="text-[0.65rem] uppercase tracking-wide"
                  >
                    {{ t('metadata.missingLocalImage') }}
                  </span>
                </div>
                <span
                  class="pill absolute left-2 top-2 max-w-[calc(100%-1rem)] truncate text-[0.65rem]"
                  :class="artistImageStatusBadgeClass(item)"
                >
                  {{ artistImageStatusBadge(item) }}
                </span>
              </div>
              <div class="space-y-2 p-3">
                <p class="truncate text-sm font-semibold">
                  {{ artistImageItemArtist(item) }}
                </p>
                <p class="truncate text-xs text-base-content/45">
                  {{ item.target || item.folder || item.file || '' }}
                </p>
                <p class="truncate text-xs text-primary">
                  {{ artistImageItemMeta(item) }}
                </p>
                <p
                  v-if="activeArtistImageTab === 'failed' && item.error"
                  class="line-clamp-3 text-xs text-error"
                >
                  {{ item.error }}
                </p>
                <button
                  v-if="showArtistImageActionButton(item)"
                  type="button"
                  class="btn btn-sm metadata-card-btn w-full border-white/10 bg-base-100/85 hover:bg-base-100"
                  :class="
                    isArtistImageUpdateTab
                      ? ''
                      : fixedArtistImages[itemKey(item)]
                      ? 'text-primary'
                      : ''
                  "
                  :disabled="applyingArtistImages[itemKey(item)]"
                  @click="
                    openArtistImagePicker(artistImageActionItem(item), {
                      context: 'artist',
                    })
                  "
                >
                  <span
                    v-if="applyingArtistImages[itemKey(item)]"
                    class="loading loading-spinner loading-xs mr-2"
                  />
                  <Icon
                    v-else
                    :icon="
                      isArtistImageUpdateTab
                        ? 'clarity:image-line'
                        : 'clarity:check-line'
                    "
                    class="mr-2 h-4 w-4"
                  />
                  {{ artistImageActionLabel(item) }}
                </button>
              </div>
            </article>
          </div>
        </div>
      </section>

      <section v-if="activeToolTab === 'artist-tags'" class="metadata-section">
        <div class="metadata-header">
          <div class="metadata-toolbar">
            <select
              v-model.number="artistTagLimit"
              class="metadata-select"
              :disabled="artistTagLoading"
              :title="t('metadata.artistTagLimit')"
            >
              <option :value="25">25</option>
              <option :value="50">50</option>
              <option :value="100">100</option>
            </select>
            <button
              class="btn btn-primary btn-sm metadata-btn px-5"
              :disabled="artistTagLoading"
              @click="scanArtistTags"
            >
              <span
                v-if="artistTagLoading"
                class="loading loading-spinner loading-xs mr-2"
              />
              <Icon v-else icon="clarity:users-line" class="h-4 w-4 mr-2" />
              {{ t('metadata.scanArtistTags') }}
            </button>
            <button
              class="btn btn-sm metadata-btn border-white/10 bg-base-100/85 hover:bg-base-100"
              :disabled="artistTagLoading"
              @click="scanAllArtistTags"
            >
              <Icon icon="clarity:fast-forward-line" class="h-4 w-4 mr-2" />
              {{ t('metadata.scanAll') }}
            </button>
            <button
              class="btn btn-sm metadata-btn border-white/10 bg-base-100/85 hover:bg-base-100"
              :disabled="artistTagItems.length === 0 || repairingAllArtistTags"
              @click="repairAllArtistTags"
            >
              <span
                v-if="repairingAllArtistTags"
                class="loading loading-spinner loading-xs mr-2"
              />
              <Icon
                v-else
                icon="clarity:check-circle-line"
                class="h-4 w-4 mr-2"
              />
              {{ t('metadata.fixAllArtistTags') }}
            </button>
          </div>
        </div>

        <div
          v-if="artistTagError"
          class="surface mb-4 flex items-start gap-3 rounded-2xl p-4 text-sm text-error"
        >
          <Icon
            icon="clarity:exclamation-circle-line"
            class="h-5 w-5 shrink-0"
          />
          <span class="min-w-0 break-words">{{ artistTagError }}</span>
        </div>

        <section class="metadata-stat-grid">
          <div class="metadata-stat-card surface rounded-2xl">
            <p class="metadata-stat-label">
              {{ t('metadata.scanned') }}
            </p>
            <p class="metadata-stat-value">
              {{ artistTagSummary.scanned }}
            </p>
          </div>
          <div class="metadata-stat-card surface rounded-2xl">
            <p class="metadata-stat-label">
              {{ t('metadata.groupedArtists') }}
            </p>
            <p class="metadata-stat-value text-primary">
              {{ artistTagItems.length }}
            </p>
          </div>
          <div class="metadata-stat-card surface rounded-2xl">
            <p class="metadata-stat-label">
              {{ t('metadata.completed') }}
            </p>
            <p class="metadata-stat-value">
              {{ completedArtistTags.length }}
            </p>
          </div>
        </section>

        <p class="mb-4 text-xs text-base-content/45">
          {{ t('metadata.artistTagsHint') }}
        </p>

        <div class="metadata-tab-shell tab-glow-shell">
          <button
            class="metadata-tab-btn"
            :class="
              activeArtistTagTab === 'needs'
                ? 'bg-primary text-primary-content shadow-glow-sm'
                : 'text-base-content/60 hover:text-base-content'
            "
            @click="activeArtistTagTab = 'needs'"
          >
            {{ t('metadata.needsFix') }}
            <span class="metadata-tab-badge">{{ artistTagItems.length }}</span>
          </button>
          <button
            class="metadata-tab-btn"
            :class="
              activeArtistTagTab === 'completed'
                ? 'bg-primary text-primary-content shadow-glow-sm'
                : 'text-base-content/60 hover:text-base-content'
            "
            @click="activeArtistTagTab = 'completed'"
          >
            {{ t('metadata.completed') }}
            <span class="metadata-tab-badge">
              {{ completedArtistTags.length }}
            </span>
          </button>
          <button
            class="metadata-tab-btn"
            :class="
              activeArtistTagTab === 'clean'
                ? 'bg-primary text-primary-content shadow-glow-sm'
                : 'text-base-content/60 hover:text-base-content'
            "
            @click="activeArtistTagTab = 'clean'"
          >
            <span class="sm:hidden">{{ t('metadata.cleanShort') }}</span>
            <span class="hidden sm:inline">{{ t('metadata.clean') }}</span>
            <span class="metadata-tab-badge">
              {{ cleanArtistTagItems.length }}
            </span>
          </button>
        </div>

        <div
          class="max-h-[34rem] overflow-x-hidden overflow-y-auto pr-1 sm:pr-2"
        >
          <div
            v-if="artistTagLoading && visibleArtistTagItems.length === 0"
            class="metadata-artist-grid"
          >
            <div
              v-for="n in 6"
              :key="n"
              class="rounded-2xl border border-white/10 bg-base-100/60 p-4"
            >
              <div class="skeleton h-5 w-2/3 rounded-full" />
              <div class="mt-4 skeleton h-20 w-full rounded-xl" />
              <div class="mt-3 skeleton h-9 w-full rounded-full" />
            </div>
          </div>

          <div
            v-else-if="visibleArtistTagItems.length === 0"
            class="surface rounded-2xl p-10 text-center"
          >
            <Icon
              icon="clarity:users-line"
              class="mx-auto mb-3 h-10 w-10 text-base-content/20"
            />
            <p class="text-sm text-base-content/50">
              {{
                artistTagLoading
                  ? t('metadata.scanning')
                  : emptyArtistTagMessage
              }}
            </p>
          </div>

          <div v-else class="metadata-artist-grid">
            <article
              v-for="item in visibleArtistTagItems"
              :key="item.file"
              class="rounded-2xl border border-primary/20 bg-base-100/75 p-4 shadow-glow-sm"
              :class="
                applyingArtistTags[item.file]
                  ? 'border-primary/40 ring-2 ring-primary/30'
                  : ''
              "
            >
              <div class="flex items-start gap-3">
                <div
                  class="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl border border-primary/20 bg-primary/10 text-primary"
                >
                  <Icon icon="clarity:users-line" class="h-6 w-6" />
                </div>
                <div class="min-w-0">
                  <p class="line-clamp-2 text-sm font-semibold">
                    {{ displaySong(item.current) }}
                  </p>
                  <p class="mt-1 truncate text-xs text-base-content/45">
                    {{ item.file }}
                  </p>
                </div>
              </div>
              <div class="mt-4 grid gap-2">
                <div
                  class="rounded-xl border border-white/10 bg-base-100/70 p-3"
                >
                  <p class="text-[0.65rem] uppercase text-base-content/45">
                    {{
                      activeArtistTagTab === 'needs'
                        ? t('metadata.currentArtists')
                        : t('metadata.verifiedArtists')
                    }}
                  </p>
                  <p class="mt-1 text-sm text-base-content/80">
                    {{ artistList(item.current?.artists) }}
                  </p>
                </div>
                <div
                  v-if="activeArtistTagTab === 'needs'"
                  class="rounded-xl border border-primary/20 bg-primary/10 p-3"
                >
                  <p class="text-[0.65rem] uppercase text-primary/80">
                    {{ t('metadata.proposedArtists') }}
                  </p>
                  <p class="mt-1 text-sm text-primary">
                    {{ artistList(item.candidate?.artists) }}
                  </p>
                </div>
              </div>
              <div
                v-if="item.folder_verification"
                class="mt-3 rounded-xl border border-primary/20 bg-base-100/70 p-3 text-xs text-base-content/60"
              >
                <p class="font-semibold text-primary">
                  {{ t('metadata.folderVerification') }}
                </p>
                <p class="mt-1">
                  {{
                    artistFolderVerificationSummary(item.folder_verification)
                  }}
                </p>
              </div>
              <button
                v-if="activeArtistTagTab === 'needs'"
                type="button"
                class="btn btn-sm metadata-card-btn mt-4 w-full border-white/10 bg-base-100/85 hover:bg-base-100"
                :class="fixedArtistTags[item.file] ? 'text-primary' : ''"
                :disabled="
                  applyingArtistTags[item.file] || fixedArtistTags[item.file]
                "
                @click="applyArtistTagRepair(item)"
              >
                <span
                  v-if="applyingArtistTags[item.file]"
                  class="loading loading-spinner loading-xs mr-2"
                />
                <Icon v-else icon="clarity:check-line" class="mr-2 h-4 w-4" />
                {{
                  applyingArtistTags[item.file]
                    ? t('metadata.fixing')
                    : fixedArtistTags[item.file]
                    ? t('metadata.fixed')
                    : t('metadata.fixArtists')
                }}
              </button>
            </article>
          </div>
        </div>
      </section>

      <section
        v-if="
          activeToolTab === 'jellyfin' &&
          sm.settings.value.enable_jellyfin_tools
        "
        class="metadata-section"
      >
        <div class="metadata-header">
          <div class="metadata-toolbar">
            <button
              class="btn btn-primary btn-sm metadata-btn px-5"
              :disabled="reconcilingArtists"
              @click="reconcileArtists"
            >
              <span
                v-if="reconcilingArtists"
                class="loading loading-spinner loading-xs mr-2"
              />
              <Icon v-else icon="clarity:user-line" class="h-4 w-4 mr-2" />
              {{ t('metadata.reconcileArtists') }}
            </button>
            <button
              class="btn btn-sm metadata-btn border-white/10 bg-base-100/85 hover:bg-base-100"
              :disabled="refreshingJellyfin"
              @click="refreshJellyfin"
            >
              <span
                v-if="refreshingJellyfin"
                class="loading loading-spinner loading-xs mr-2"
              />
              <Icon v-else icon="clarity:sync-line" class="h-4 w-4 mr-2" />
              {{ t('metadata.refreshJellyfin') }}
            </button>
            <button
              class="btn btn-sm metadata-btn border-white/10 bg-base-100/85 hover:bg-base-100"
              :disabled="
                repairingAllJellyfin ||
                reconcilingArtists ||
                allJellyfinRepairableItems.length === 0
              "
              @click="repairAllJellyfinArtistImages"
            >
              <span
                v-if="repairingAllJellyfin"
                class="loading loading-spinner loading-xs mr-2"
              />
              <Icon v-else icon="clarity:image-line" class="h-4 w-4 mr-2" />
              {{ t('metadata.fixAllArtistImages') }}
            </button>
          </div>
        </div>

        <div class="metadata-stat-grid-4">
          <div class="metadata-stat-card surface rounded-2xl">
            <p class="metadata-stat-label">
              {{ t('metadata.jellyfinLibrary') }}
            </p>
            <p class="metadata-stat-value metadata-stat-value-text">
              {{ jellyfinLibraryName }}
            </p>
          </div>
          <div class="metadata-stat-card surface rounded-2xl">
            <p class="metadata-stat-label">
              {{ t('metadata.jellyfinArtists') }}
            </p>
            <p class="metadata-stat-value text-primary">
              {{ jellyfinRepairableItems.length }}
            </p>
          </div>
          <div class="metadata-stat-card surface rounded-2xl">
            <p class="metadata-stat-label">
              {{ t('metadata.localArtistFolders') }}
            </p>
            <p class="metadata-stat-value">
              {{ jellyfinCounts.folders }}
            </p>
            <button
              v-if="artistReconciliation"
              class="btn btn-primary btn-xs metadata-stat-action"
              :disabled="
                repairingJellyfinBucket === 'folder_only' ||
                repairingAllJellyfin ||
                reconcilingArtists ||
                jellyfinRepairableBucketItems('folder_only').length === 0
              "
              :title="t('metadata.bulkFixGroup')"
              @click="repairJellyfinBucket('folder_only')"
            >
              <span
                v-if="repairingJellyfinBucket === 'folder_only'"
                class="loading loading-spinner loading-xs"
              />
              <Icon
                v-else
                icon="clarity:magic-wand-line"
                class="h-4 w-4 shrink-0"
              />
              <span
                v-if="repairingJellyfinBucket !== 'folder_only'"
                class="metadata-stat-action-label"
              >
                <span class="sm:hidden">{{ t('metadata.bulkFixShort') }}</span>
                <span class="hidden sm:inline">{{
                  t('metadata.bulkFixGroup')
                }}</span>
              </span>
            </button>
          </div>
          <div class="metadata-stat-card surface rounded-2xl">
            <p class="metadata-stat-label">
              {{ t('metadata.missingLocalImages') }}
            </p>
            <p class="metadata-stat-value text-primary">
              {{ jellyfinCounts.missingImages }}
            </p>
            <button
              v-if="artistReconciliation"
              class="btn btn-primary btn-xs metadata-stat-action"
              :disabled="
                repairingJellyfinBucket === 'missing_images' ||
                repairingAllJellyfin ||
                reconcilingArtists ||
                jellyfinRepairableBucketItems('missing_images').length === 0
              "
              :title="t('metadata.bulkFixGroup')"
              @click="repairJellyfinBucket('missing_images')"
            >
              <span
                v-if="repairingJellyfinBucket === 'missing_images'"
                class="loading loading-spinner loading-xs"
              />
              <Icon
                v-else
                icon="clarity:magic-wand-line"
                class="h-4 w-4 shrink-0"
              />
              <span
                v-if="repairingJellyfinBucket !== 'missing_images'"
                class="metadata-stat-action-label"
              >
                <span class="sm:hidden">{{ t('metadata.bulkFixShort') }}</span>
                <span class="hidden sm:inline">{{
                  t('metadata.bulkFixGroup')
                }}</span>
              </span>
            </button>
          </div>
        </div>

        <div
          v-if="jellyfinMessage"
          class="surface mb-5 flex items-start gap-3 rounded-2xl p-4 text-sm"
          :class="jellyfinError ? 'text-error' : 'text-primary'"
        >
          <Icon
            :icon="
              jellyfinError
                ? 'clarity:exclamation-circle-line'
                : 'clarity:check-circle-line'
            "
            class="h-5 w-5 shrink-0"
          />
          <span class="min-w-0 break-words">{{ jellyfinMessage }}</span>
        </div>

        <div
          v-if="artistReconciliation"
          class="metadata-header mb-5 sm:items-center"
        >
          <h3 class="text-sm font-semibold text-base-content/80">
            {{ t('metadata.artistReconciliation') }}
          </h3>
          <p class="text-xs text-base-content/45">
            {{ t('metadata.lastChecked') }} {{ lastReconciled }}
          </p>
        </div>

        <div
          v-if="reconcilingArtists"
          class="surface scan-skeleton-glow rounded-2xl p-10 text-center"
        >
          <span class="loading loading-spinner loading-md text-primary" />
          <p class="mt-4 text-sm font-medium text-base-content/70">
            {{ t('metadata.reconcilingArtists') }}
          </p>
          <p class="mt-1 text-xs text-base-content/45">
            {{ t('metadata.reconcilingArtistsHint') }}
          </p>
        </div>

        <div
          v-else-if="artistReconciliation"
          class="surface min-w-0 rounded-2xl p-3 sm:p-4"
        >
          <div class="metadata-bucket-grid">
            <button
              v-for="bucket in reconciliationBuckets"
              :key="bucket.key"
              type="button"
              class="metadata-bucket-btn rounded-2xl border border-primary/20 bg-base-100/70 p-3 text-left transition-colors hover:border-primary/45 hover:bg-base-100/90"
              :class="
                activeReconciliationBucket === bucket.key
                  ? 'border-primary/60 shadow-glow-sm'
                  : ''
              "
              @click="activeReconciliationBucket = bucket.key"
            >
              <div class="flex items-start justify-between gap-3">
                <div>
                  <p class="text-xs uppercase text-base-content/40">
                    {{ bucket.label }}
                  </p>
                  <p class="mt-1 text-2xl font-semibold text-primary">
                    {{ bucket.count }}
                  </p>
                  <p
                    v-if="bucket.repairableCount > 0"
                    class="mt-2 text-[11px] font-medium text-primary"
                  >
                    {{
                      t('metadata.bulkFixAvailable', {
                        count: bucket.repairableCount,
                      })
                    }}
                  </p>
                </div>
                <Icon :icon="bucket.icon" class="h-5 w-5 text-primary/70" />
              </div>
            </button>
          </div>

          <div v-if="activeReconciliationBucketMeta" class="metadata-bulk-bar">
            <div class="min-w-0">
              <p class="text-sm font-semibold">
                {{ activeReconciliationBucketMeta.label }}
              </p>
              <p class="text-xs text-base-content/45">
                {{
                  activeReconciliationBucket === 'tag_only'
                    ? t('metadata.bulkFixTagsReady', {
                        count: activeReconciliationBucketMeta.repairableCount,
                      })
                    : t('metadata.bulkFixReady', {
                        count: activeReconciliationBucketMeta.repairableCount,
                      })
                }}
              </p>
            </div>
            <button
              class="btn btn-primary btn-sm metadata-btn h-9 px-4 sm:w-auto"
              :disabled="
                repairingJellyfinBucket === activeReconciliationBucket ||
                repairingAllJellyfin ||
                reconcilingArtists ||
                activeReconciliationBucketMeta.repairableCount === 0
              "
              @click="repairJellyfinBucket(activeReconciliationBucket)"
            >
              <span
                v-if="repairingJellyfinBucket === activeReconciliationBucket"
                class="loading loading-spinner loading-xs mr-2"
              />
              <Icon
                v-else
                icon="clarity:magic-wand-line"
                class="h-4 w-4 mr-2"
              />
              {{ t('metadata.bulkFixGroup') }}
            </button>
          </div>

          <div
            v-if="reconciliationGridItems.length > 0"
            class="max-h-[34rem] overflow-x-hidden overflow-y-auto pr-1"
          >
            <div class="metadata-artist-grid">
              <article
                v-for="item in reconciliationGridItems"
                :key="`${item.bucketKey}-${item.name}`"
                class="overflow-hidden rounded-2xl border border-primary/20 bg-base-100/75 shadow-glow-sm"
              >
                <div class="relative aspect-square bg-base-100/80">
                  <img
                    v-if="jellyfinPreviewSrc(item)"
                    :src="jellyfinPreviewSrc(item)"
                    :alt="item.name"
                    class="h-full w-full object-cover"
                    loading="lazy"
                    @error="markJellyfinPreviewFailed(item)"
                  />
                  <div
                    v-else
                    class="flex h-full w-full items-center justify-center bg-primary/5"
                  >
                    <Icon
                      icon="clarity:image-line"
                      class="h-10 w-10 text-base-content/25"
                    />
                  </div>
                  <div
                    v-if="applyingArtistImages[jellyfinRepairKey(item)]"
                    class="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-base-100/80 px-3 text-center"
                  >
                    <span
                      class="loading loading-spinner loading-md text-primary"
                    />
                    <p class="text-[11px] font-medium text-base-content/70">
                      {{ t('metadata.fixing') }}
                    </p>
                  </div>
                </div>
                <div class="p-3">
                  <p class="truncate text-sm font-semibold">
                    {{ item.name }}
                  </p>
                  <div class="mt-2 flex flex-wrap items-center gap-2">
                    <span
                      class="pill truncate text-[11px]"
                      :class="
                        item.has_image
                          ? 'badge-soft'
                          : 'bg-warning/10 text-warning'
                      "
                    >
                      {{
                        item.has_image
                          ? t('metadata.localImageReady')
                          : t('metadata.missingLocalImage')
                      }}
                    </span>
                    <span
                      v-if="failedArtistRepairKeys[jellyfinRepairKey(item)]"
                      class="pill truncate text-[11px] bg-error/10 text-error"
                    >
                      {{ t('metadata.fixFailed') }}
                    </span>
                  </div>
                  <div class="mt-2 flex items-center justify-between gap-2">
                    <span class="pill max-w-full truncate text-[11px]">
                      {{ item.bucketLabel }}
                    </span>
                    <Icon
                      :icon="item.icon"
                      class="h-4 w-4 shrink-0 text-primary/70"
                    />
                  </div>
                  <button
                    v-if="isJellyfinTagRepairItem(item)"
                    class="btn btn-primary btn-xs metadata-card-btn"
                    :disabled="applying[item.file] || fixed[item.file]"
                    @click="applyJellyfinMetadataRepair(item)"
                  >
                    <span
                      v-if="applying[item.file]"
                      class="loading loading-spinner loading-xs mr-2"
                    />
                    <Icon v-else icon="clarity:tag-line" class="h-4 w-4 mr-2" />
                    {{
                      fixed[item.file]
                        ? t('metadata.fixed')
                        : applying[item.file]
                        ? t('metadata.fixing')
                        : t('metadata.fixTags')
                    }}
                  </button>
                  <button
                    v-else-if="isJellyfinRepairableItem(item)"
                    class="btn btn-primary btn-xs metadata-card-btn"
                    :disabled="
                      applyingArtistImages[jellyfinRepairKey(item)] ||
                      fixedArtistImages[jellyfinRepairKey(item)]
                    "
                    @click="
                      openArtistImagePicker(item, { context: 'jellyfin' })
                    "
                  >
                    <span
                      v-if="applyingArtistImages[jellyfinRepairKey(item)]"
                      class="loading loading-spinner loading-xs mr-2"
                    />
                    <Icon
                      v-else
                      icon="clarity:image-line"
                      class="h-4 w-4 mr-2"
                    />
                    {{
                      fixedArtistImages[jellyfinRepairKey(item)]
                        ? t('metadata.fixed')
                        : failedArtistRepairKeys[jellyfinRepairKey(item)]
                        ? t('metadata.fixFailed')
                        : t('metadata.chooseCover')
                    }}
                  </button>
                  <button
                    v-else-if="canUpdateJellyfinArtistImage(item)"
                    class="btn btn-sm metadata-card-btn w-full border-white/10 bg-base-100/85 hover:bg-base-100"
                    :disabled="applyingArtistImages[jellyfinRepairKey(item)]"
                    @click="
                      openArtistImagePicker(item, { context: 'jellyfin' })
                    "
                  >
                    <span
                      v-if="applyingArtistImages[jellyfinRepairKey(item)]"
                      class="loading loading-spinner loading-xs mr-2"
                    />
                    <Icon
                      v-else
                      icon="clarity:refresh-line"
                      class="mr-2 h-4 w-4"
                    />
                    {{
                      applyingArtistImages[jellyfinRepairKey(item)]
                        ? t('metadata.fixing')
                        : t('metadata.updateCover')
                    }}
                  </button>
                  <p
                    v-else-if="item.missing_image"
                    class="mt-3 text-[11px] leading-snug text-base-content/45"
                  >
                    {{ t('metadata.noRepairFile') }}
                  </p>
                </div>
              </article>
            </div>
          </div>

          <div
            v-else
            class="rounded-2xl border border-white/10 bg-base-100/60 p-8 text-center"
          >
            <Icon
              icon="clarity:user-line"
              class="mx-auto mb-3 h-10 w-10 text-base-content/20"
            />
            <p class="text-sm text-base-content/50">
              {{ t('metadata.noArtistsInBucket') }}
            </p>
          </div>
        </div>

        <div
          v-else
          class="surface rounded-2xl p-8 text-center text-sm text-base-content/50"
        >
          <Icon
            icon="clarity:compare-line"
            class="mx-auto mb-3 h-10 w-10 text-base-content/20"
          />
          <p>{{ t('metadata.emptyReconciliation') }}</p>
        </div>
      </section>
    </main>

    <div
      v-if="albumArtistModalOpen"
      class="fixed inset-0 z-40 flex items-end justify-center bg-black/60 p-4 sm:items-center"
      @click.self="closeAlbumArtistModal"
    >
      <div
        class="surface-strong flex max-h-[88dvh] w-full max-w-4xl flex-col overflow-hidden rounded-3xl border border-white/10 shadow-glow-md"
        role="dialog"
        aria-modal="true"
      >
        <div
          class="flex items-center justify-between gap-4 border-b border-white/10 px-5 py-4"
        >
          <div class="min-w-0">
            <h3 class="truncate text-lg font-semibold">
              {{ selectedAlbumArtist?.name }}
            </h3>
            <p class="mt-1 text-sm text-base-content/55">
              {{
                t('metadata.artistAlbumCount', {
                  count: selectedAlbumArtistAlbums.length,
                })
              }}
            </p>
          </div>
          <button
            type="button"
            class="icon-btn shrink-0"
            @click="closeAlbumArtistModal"
          >
            <Icon icon="clarity:times-line" class="h-5 w-5" />
          </button>
        </div>

        <div class="min-h-0 overflow-y-auto p-4 sm:p-5">
          <div class="grid gap-3 sm:grid-cols-2">
            <article
              v-for="album in selectedAlbumArtistAlbums"
              :key="album.key"
              class="rounded-2xl border border-white/10 bg-base-100/70 p-3"
            >
              <button
                type="button"
                class="group flex w-full min-w-0 items-center gap-3 text-left"
                @click="openAlbumImagePicker(albumImageActionItem(album))"
              >
                <div
                  class="relative h-20 w-20 shrink-0 overflow-hidden rounded-xl bg-primary/10"
                >
                  <img
                    v-if="albumCoverUrl(album)"
                    :src="albumCoverUrl(album)"
                    :alt="album.name"
                    class="h-full w-full object-cover"
                    loading="lazy"
                  />
                  <div
                    v-else
                    class="flex h-full w-full items-center justify-center text-base-content/30"
                  >
                    <Icon icon="clarity:image-line" class="h-8 w-8" />
                  </div>
                </div>
                <div class="min-w-0 flex-1">
                  <p
                    class="truncate text-sm font-semibold group-hover:text-primary"
                  >
                    {{ album.name }}
                  </p>
                  <p class="mt-1 text-xs text-base-content/45">
                    {{ t('player.countMany', { count: album.files.length }) }}
                  </p>
                </div>
              </button>
              <button
                type="button"
                class="btn btn-primary btn-sm metadata-card-btn mt-3 w-full"
                :disabled="applyingAlbumImages[album.coverFile]"
                @click="openAlbumImagePicker(albumImageActionItem(album))"
              >
                <span
                  v-if="applyingAlbumImages[album.coverFile]"
                  class="loading loading-spinner loading-xs mr-2"
                />
                <Icon v-else icon="clarity:image-line" class="mr-2 h-4 w-4" />
                {{ t('metadata.updateCover') }}
              </button>
            </article>
          </div>
        </div>
      </div>
    </div>

    <div
      v-if="artistImagePickerOpen"
      class="fixed inset-0 z-50 flex items-end justify-center bg-black/60 p-4 sm:items-center"
      @click.self="closeArtistImagePicker"
    >
      <div
        class="surface-strong w-full max-w-3xl overflow-hidden rounded-3xl border border-white/10 shadow-glow-md"
        role="dialog"
        aria-modal="true"
      >
        <div class="border-b border-white/10 px-5 py-4">
          <h3 class="text-lg font-semibold">
            {{
              artistImagePickerContext === 'album'
                ? t('metadata.chooseAlbumCoverTitle')
                : t('metadata.chooseCoverTitle')
            }}
          </h3>
          <p class="mt-1 text-sm text-base-content/60">
            {{
              artistImagePickerItem?.name ||
              artistImagePickerItem?.album_name ||
              artistImagePickerItem?.artist
            }}
          </p>
          <p class="mt-1 text-xs text-base-content/45">
            {{ t('metadata.chooseCoverHint') }}
          </p>
        </div>

        <div class="max-h-[28rem] overflow-y-auto px-5 py-4">
          <div
            v-if="artistImagePickerLoading"
            class="flex min-h-40 flex-col items-center justify-center gap-3 px-4 text-center text-sm text-base-content/60"
          >
            <span class="loading loading-spinner loading-md text-primary" />
            <p>{{ t('metadata.chooseCoverLoading') }}</p>
            <p
              v-if="artistImagePickerSlowHint"
              class="text-xs text-base-content/45"
            >
              {{ t('metadata.chooseCoverLoadingSlow') }}
            </p>
          </div>
          <p
            v-else-if="artistImagePickerError"
            class="rounded-2xl border border-error/20 bg-error/10 px-4 py-3 text-sm text-error"
          >
            {{ artistImagePickerError }}
          </p>
          <p
            v-else-if="artistImagePickerOptions.length === 0"
            class="rounded-2xl border border-white/10 bg-base-100/60 px-4 py-8 text-center text-sm text-base-content/55"
          >
            {{
              artistImagePickerContext === 'album'
                ? t('metadata.chooseAlbumCoverEmpty')
                : t('metadata.chooseCoverEmpty')
            }}
          </p>
          <div v-else class="grid grid-cols-2 gap-3 sm:grid-cols-3">
            <button
              v-for="option in artistImagePickerOptions"
              :key="option.id"
              type="button"
              class="overflow-hidden rounded-2xl border text-left transition"
              :class="
                artistImagePickerSelected?.id === option.id
                  ? 'border-primary ring-2 ring-primary/40'
                  : 'border-white/10 hover:border-primary/30'
              "
              @click="artistImagePickerSelected = option"
            >
              <div
                class="relative flex aspect-square items-center justify-center overflow-hidden bg-base-100/80"
              >
                <img
                  v-if="
                    option.preview_url &&
                    !isArtistImagePickerPreviewFailed(option.id)
                  "
                  :src="apiPreviewSrc(option.preview_url)"
                  :alt="option.label"
                  class="h-full w-full object-cover"
                  loading="lazy"
                  @error="markArtistImagePickerPreviewFailed(option.id)"
                />
                <div
                  v-else
                  class="flex flex-col items-center gap-2 px-3 text-center text-base-content/45"
                >
                  <Icon icon="clarity:image-off-line" class="h-10 w-10" />
                  <span class="text-xs">
                    {{ t('metadata.chooseCoverPreviewUnavailable') }}
                  </span>
                </div>
              </div>
              <div class="space-y-1 p-3">
                <p class="truncate text-sm font-medium">{{ option.label }}</p>
                <p class="truncate text-[11px] text-base-content/55">
                  {{ option.source }}
                </p>
                <p
                  v-if="option.subtitle"
                  class="truncate text-[11px] text-base-content/40"
                >
                  {{ option.subtitle }}
                </p>
              </div>
            </button>
          </div>
        </div>

        <div
          class="flex flex-col gap-2 border-t border-white/10 px-5 py-4 sm:flex-row sm:justify-end"
        >
          <button
            type="button"
            class="btn btn-ghost metadata-btn"
            @click="closeArtistImagePicker"
          >
            {{ t('common.cancel') }}
          </button>
          <button
            type="button"
            class="btn btn-primary metadata-btn"
            :disabled="!artistImagePickerSelected || artistImagePickerApplying"
            @click="confirmArtistImageSelection"
          >
            <span
              v-if="artistImagePickerApplying"
              class="loading loading-spinner loading-xs mr-2"
            />
            {{ t('metadata.applySelectedCover') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { Icon } from '@iconify/vue'

import Navbar from '/src/components/Navbar.vue'
import API from '/src/model/api'
import { groupAlbums, groupArtists } from '/src/model/library'
import { useSettingsManager } from '/src/model/settings'
import { useI18n } from '/src/i18n'

const { t } = useI18n()
const sm = useSettingsManager()
const JELLYFIN_IMAGE_REPAIR_BUCKETS = [
  'missing_images',
  'jellyfin_only',
  'folder_only',
]
const activeToolTab = ref('metadata')
const metadataToolMenuOpen = ref(false)
const loading = ref(false)
const error = ref('')
const items = ref([])
const cleanItems = ref([])
const applying = ref({})
const fixed = ref({})
const metadataCoverFailed = ref({})
const completedItems = ref([])
const activeTab = ref('needs')
const repairingAll = ref(false)
const scanLimit = ref(25)
const summary = ref({ scanned: 0, matched: 0, total: 0 })
const artistImageLoading = ref(false)
const artistImageError = ref('')
const artistImageLimit = ref(50)
const artistImageItems = ref([])
const cleanArtistImageItems = ref([])
const completedArtistImages = ref([])
const failedArtistImages = ref([])
const activeArtistImageTab = ref('needs')
const applyingArtistImages = ref({})
const fixedArtistImages = ref({})
const failedArtistRepairKeys = ref({})
const jellyfinPreviewFailed = ref({})
const artistImagePickerOpen = ref(false)
const artistImagePickerContext = ref('artist')
const artistImagePickerItem = ref(null)
const artistImagePickerOptions = ref([])
const artistImagePickerSelected = ref(null)
const artistImagePickerLoading = ref(false)
const artistImagePickerApplying = ref(false)
const artistImagePickerError = ref('')
const artistImagePickerSlowHint = ref(false)
const artistImagePickerPreviewFailed = ref({})
let artistImagePickerSlowTimer = null
const repairingAllImages = ref(false)
const artistImageSummary = ref({ scanned: 0, matched: 0, total: 0 })
const albumImageLoading = ref(false)
const albumImageError = ref('')
const albumImageLimit = ref(50)
const albumImageItems = ref([])
const cleanAlbumImageItems = ref([])
const completedAlbumImages = ref([])
const activeAlbumImageTab = ref('needs')
const applyingAlbumImages = ref({})
const fixedAlbumImages = ref({})
const repairingAllAlbumImages = ref(false)
const albumImageSummary = ref({
  scanned: 0,
  scannedAlbums: 0,
  scannedTracks: 0,
  matched: 0,
  total: 0,
  trackTotal: 0,
})
const albumImageLibraryItems = ref([])
const albumImageArtistQuery = ref('')
const albumArtistModalOpen = ref(false)
const selectedAlbumArtist = ref(null)
const artistTagLoading = ref(false)
const artistTagError = ref('')
const artistTagLimit = ref(50)
const artistTagItems = ref([])
const cleanArtistTagItems = ref([])
const completedArtistTags = ref([])
const activeArtistTagTab = ref('needs')
const applyingArtistTags = ref({})
const fixedArtistTags = ref({})
const repairingAllArtistTags = ref(false)
const artistTagSummary = ref({ scanned: 0, matched: 0, total: 0 })
const artistReconciliation = ref(null)
const activeReconciliationBucket = ref('missing_images')
const reconcilingArtists = ref(false)
const refreshingJellyfin = ref(false)
const repairingAllJellyfin = ref(false)
const repairingJellyfinBucket = ref('')
const jellyfinMessage = ref('')
const jellyfinError = ref(false)
const lastReconciled = ref('')
let pollTimer = null
let artistImagePollTimer = null
let albumImagePollTimer = null
let artistTagPollTimer = null

const visibleItems = computed(() =>
  activeTab.value === 'completed'
    ? completedItems.value
    : activeTab.value === 'clean'
    ? cleanItems.value
    : items.value
)

const metadataToolTabs = computed(() => {
  const tabs = [
    {
      id: 'metadata',
      label: t('metadata.metadataTab'),
      icon: 'clarity:tag-line',
    },
    {
      id: 'album-images',
      label: t('metadata.albumImagesTab'),
      icon: 'clarity:library-line',
    },
    {
      id: 'images',
      label: t('metadata.artistImagesTab'),
      icon: 'clarity:image-line',
    },
    {
      id: 'artist-tags',
      label: t('metadata.artistRepairTab'),
      icon: 'clarity:users-line',
    },
  ]
  if (sm.settings.value.enable_jellyfin_tools) {
    tabs.push({
      id: 'jellyfin',
      label: t('metadata.jellyfinTab'),
      icon: 'clarity:server-line',
    })
  }
  return tabs
})

const useMobileToolMenu = computed(() => metadataToolTabs.value.length > 4)

const visibleArtistImageItems = computed(() =>
  activeArtistImageTab.value === 'completed'
    ? completedArtistImages.value
    : activeArtistImageTab.value === 'clean'
    ? cleanArtistImageItems.value
    : activeArtistImageTab.value === 'failed'
    ? failedArtistImages.value
    : artistImageItems.value
)

const visibleAlbumImageItems = computed(() =>
  activeAlbumImageTab.value === 'completed'
    ? completedAlbumImages.value
    : activeAlbumImageTab.value === 'clean'
    ? cleanAlbumImageItems.value
    : albumImageItems.value
)

const hasAlbumImageScanData = computed(
  () =>
    albumImageItems.value.length > 0 ||
    cleanAlbumImageItems.value.length > 0 ||
    completedAlbumImages.value.length > 0 ||
    albumImageSummary.value.scanned > 0
)

const libraryGroupOptions = computed(() => ({
  unknownArtist: t('common.unknownArtist'),
}))

const albumImageArtists = computed(() =>
  groupArtists(albumImageBrowserItems.value, libraryGroupOptions.value).filter(
    (artist) => albumImageAlbumsForArtist(artist).length > 0
  )
)

const filteredAlbumImageArtists = computed(() => {
  const query = albumImageArtistQuery.value.trim().toLowerCase()
  if (!query) return albumImageArtists.value
  return albumImageArtists.value.filter((artist) => {
    const artistName = String(artist?.name || '').toLowerCase()
    if (artistName.includes(query)) return true
    return albumImageAlbumsForArtist(artist).some((album) =>
      String(album?.name || '')
        .toLowerCase()
        .includes(query)
    )
  })
})

const albumImageAlbums = computed(() =>
  groupAlbums(albumImageBrowserItems.value, libraryGroupOptions.value)
)

const albumImageBrowserItems = computed(() => {
  const byFile = new Map()
  if (!hasAlbumImageScanData.value) {
    for (const item of albumImageLibraryItems.value) {
      if (item?.file) byFile.set(item.file, item)
    }
  }
  for (const item of visibleAlbumImageItems.value) {
    const converted = albumImageScanItemToLibraryItem(item)
    if (converted?.file) {
      byFile.set(converted.file, {
        ...(albumImageLibraryItems.value.find(
          (libraryItem) => libraryItem?.file === converted.file
        ) || {}),
        ...converted,
      })
    }
  }
  return Array.from(byFile.values())
})

const selectedAlbumArtistAlbums = computed(() =>
  selectedAlbumArtist.value
    ? albumImageAlbumsForArtist(selectedAlbumArtist.value)
    : []
)

const visibleArtistTagItems = computed(() =>
  activeArtistTagTab.value === 'completed'
    ? completedArtistTags.value
    : activeArtistTagTab.value === 'clean'
    ? cleanArtistTagItems.value
    : artistTagItems.value
)

const emptyArtistTagMessage = computed(() => {
  if (activeArtistTagTab.value === 'completed') {
    return t('metadata.emptyArtistTagCompleted')
  }
  if (activeArtistTagTab.value === 'clean') {
    return t('metadata.emptyArtistTagClean')
  }
  return t('metadata.emptyArtistTags')
})

const isArtistImageUpdateTab = computed(() =>
  ['clean', 'completed'].includes(activeArtistImageTab.value)
)

const emptyArtistImageMessage = computed(() => {
  if (activeArtistImageTab.value === 'completed') {
    return t('metadata.emptyArtistImageCompleted')
  }
  if (activeArtistImageTab.value === 'clean') {
    return t('metadata.emptyArtistImageClean')
  }
  if (activeArtistImageTab.value === 'failed') {
    return t('metadata.emptyArtistImageFailed')
  }
  return t('metadata.emptyArtistImages')
})

const emptyAlbumImageMessage = computed(() => {
  if (activeAlbumImageTab.value === 'completed') {
    return t('metadata.emptyAlbumImageCompleted')
  }
  if (activeAlbumImageTab.value === 'clean') {
    return t('metadata.emptyAlbumImageClean')
  }
  return t('metadata.emptyAlbumImages')
})

const reconciliationBuckets = computed(() => {
  const data = artistReconciliation.value || {}
  const buckets = [
    {
      key: 'missing_images',
      label: t('metadata.missingLocalImages'),
      items: data.missing_images || [],
      count: data.counts?.missing_local_images || 0,
      icon: 'clarity:image-line',
    },
    {
      key: 'jellyfin_only',
      label: t('metadata.jellyfinOnly'),
      items: data.jellyfin_only || [],
      count: data.counts?.jellyfin_only || 0,
      icon: 'clarity:cloud-line',
    },
    {
      key: 'folder_only',
      label: t('metadata.folderOnly'),
      items: data.folder_only || [],
      count: data.counts?.folder_only || 0,
      icon: 'clarity:folder-line',
    },
    {
      key: 'tag_only',
      label: t('metadata.tagOnly'),
      items: data.tag_only || [],
      count: data.counts?.tag_only || 0,
      icon: 'clarity:tag-line',
    },
    {
      key: 'matched',
      label: t('metadata.matchedArtists'),
      items: data.matched || [],
      count: data.counts?.matched || 0,
      icon: 'clarity:check-circle-line',
    },
  ]
  return buckets.map((bucket) => ({
    ...bucket,
    repairableCount:
      bucket.key === 'tag_only'
        ? jellyfinTagRepairableBucketItems(bucket.key).length
        : jellyfinRepairableBucketItems(bucket.key).length,
  }))
})

const reconciliationGridItems = computed(() =>
  reconciliationBuckets.value
    .filter((bucket) => bucket.key === activeReconciliationBucket.value)
    .flatMap((bucket) =>
      (bucket.items || []).map((item) => ({
        ...item,
        bucketKey: bucket.key,
        bucketLabel: bucket.label,
        icon: bucket.icon,
      }))
    )
)

const jellyfinCounts = computed(() => {
  const counts = artistReconciliation.value?.counts || {}
  return {
    jellyfin: counts.jellyfin || 0,
    folders: counts.folders || 0,
    tags: counts.tags || 0,
    jellyfinOnly: counts.jellyfin_only || 0,
    missingImages: counts.missing_local_images || 0,
  }
})

const jellyfinLibraryName = computed(() => {
  const library = artistReconciliation.value?.library || {}
  return library.name || library.id || t('metadata.notCheckedYet')
})

const jellyfinRepairableItems = computed(() =>
  jellyfinRepairableBucketItems('missing_images')
)

const allJellyfinRepairableItems = computed(() => {
  const itemsByKey = new Map()
  for (const bucketKey of JELLYFIN_IMAGE_REPAIR_BUCKETS) {
    for (const item of jellyfinRepairableBucketItems(bucketKey)) {
      itemsByKey.set(jellyfinRepairKey(item), item)
    }
  }
  return [...itemsByKey.values()]
})

const activeReconciliationBucketMeta = computed(() =>
  reconciliationBuckets.value.find(
    (bucket) => bucket.key === activeReconciliationBucket.value
  )
)

watch(
  () => sm.settings.value.enable_jellyfin_tools,
  (enabled) => {
    if (!enabled && activeToolTab.value === 'jellyfin') {
      activeToolTab.value = 'metadata'
    }
  }
)

watch(
  useMobileToolMenu,
  () => {
    syncMetadataMobileAction()
  },
  { immediate: true }
)

watch(activeToolTab, (tabId) => {
  metadataToolMenuOpen.value = false
  if (tabId === 'album-images') {
    refreshAlbumImageStatus()
    loadAlbumImageLibrary()
  }
})

function selectToolTab(tabId) {
  activeToolTab.value = tabId
  metadataToolMenuOpen.value = false
}

function syncMetadataMobileAction() {
  if (typeof window === 'undefined') return
  if (!useMobileToolMenu.value) {
    clearMetadataMobileAction()
    return
  }
  window.dispatchEvent(
    new CustomEvent('downtify:mobile-route-action', {
      detail: {
        routeName: 'Metadata',
        icon: 'clarity:menu-line',
        label: t('metadata.toolsMenu'),
        title: t('metadata.toolsMenu'),
        onClick: () => {
          metadataToolMenuOpen.value = !metadataToolMenuOpen.value
        },
      },
    })
  )
}

function clearMetadataMobileAction() {
  if (typeof window === 'undefined') return
  window.dispatchEvent(
    new CustomEvent('downtify:clear-mobile-route-action', {
      detail: { routeName: 'Metadata' },
    })
  )
}

function displaySong(song) {
  const artists = (song?.artists || []).join(', ')
  const title = song?.name || t('common.unknownTrack')
  const album = song?.album_name ? ` - ${song.album_name}` : ''
  return `${artists || t('common.unknownArtist')} - ${title}${album}`
}

function artistList(artists) {
  const values = (artists || []).filter(Boolean)
  return values.length > 0 ? values.join(', ') : t('common.unknownArtist')
}

function artistFolderVerificationSummary(verification) {
  const created = verification?.created_folders?.length || 0
  const removed = verification?.removed_folders?.length || 0
  const remaining = verification?.old_folders_remaining?.length || 0
  if (remaining > 0) {
    return t('metadata.artistFolderVerifiedPartial')
      .replace('{created}', String(created))
      .replace('{remaining}', String(remaining))
  }
  return t('metadata.artistFolderVerified')
    .replace('{created}', String(created))
    .replace('{removed}', String(removed))
}

function metadataCoverUrl(item) {
  const file = String(item?.file || '').trim()
  if (!file || metadataCoverFailed.value[file]) {
    return ''
  }
  return apiPreviewSrc(API.coverFileURL(file, 0))
}

function markMetadataCoverFailed(file) {
  metadataCoverFailed.value = {
    ...metadataCoverFailed.value,
    [file]: true,
  }
}

function metadataStatusBadge() {
  if (activeTab.value === 'completed') {
    return t('metadata.fixed')
  }
  if (activeTab.value === 'clean') {
    return t('metadata.clean')
  }
  return t('metadata.needsFix')
}

function metadataStatusBadgeClass() {
  if (activeTab.value === 'completed') {
    return 'badge-success text-success-content'
  }
  if (activeTab.value === 'clean') {
    return 'badge-soft'
  }
  return 'badge-warning text-warning-content'
}

function albumImagePreviewUrl(item) {
  const candidateCover = String(item?.candidate?.cover_url || '').trim()
  if (candidateCover) {
    return API.remoteCoverSources(candidateCover, 320).src
  }
  const file = String(item?.file || '').trim()
  return file ? apiPreviewSrc(API.coverFileURL(file, 320)) : ''
}

function albumCoverUrl(album) {
  const file = String(album?.coverFile || album?.file || '').trim()
  return file ? apiPreviewSrc(API.coverFileURL(file, 320)) : ''
}

function albumArtistCoverUrl(artist) {
  const file = String(artist?.previewFiles?.[0] || artist?.files?.[0] || '')
  return file ? apiPreviewSrc(API.coverFileURL(file, 320)) : ''
}

function albumImageAlbumsForArtist(artist) {
  const name = String(artist?.name || '').trim()
  return albumImageAlbums.value.filter((album) => album.artist === name)
}

function albumImageScanItemToLibraryItem(item) {
  const current = item?.current || {}
  const candidate = item?.candidate || {}
  const file = String(item?.file || '').trim()
  if (!file) return null
  const artists =
    current.artists ||
    candidate.artists ||
    [current.artist || candidate.artist].filter(Boolean)
  return {
    file,
    title: current.name || candidate.name || '',
    artist: artists?.[0] || current.artist || candidate.artist || '',
    artists,
    album: current.album_name || candidate.album_name || '',
    genre: current.genre || candidate.genre || '',
    browse_genre: current.browse_genre || candidate.browse_genre || '',
  }
}

function openAlbumArtistModal(artist) {
  selectedAlbumArtist.value = artist
  albumArtistModalOpen.value = true
}

function closeAlbumArtistModal() {
  albumArtistModalOpen.value = false
  selectedAlbumArtist.value = null
}

function albumImageActionItem(item) {
  const file = String(item?.coverFile || item?.file || item?.files?.[0] || '')
  const current = item?.current || {
    name: item?.name || '',
    album_name: item?.name || '',
    artists: item?.artists || [item?.artist].filter(Boolean),
  }
  return {
    ...item,
    file,
    current,
    name: item?.name || current.album_name || current.name || '',
    artist: item?.artist || current.artist || current.artists?.[0] || '',
    album_name: item?.name || current.album_name || '',
    artists: item?.artists || current.artists || [item?.artist].filter(Boolean),
  }
}

function albumImageStatusBadge(item) {
  if (activeAlbumImageTab.value === 'completed') {
    return t('metadata.completed')
  }
  if (activeAlbumImageTab.value === 'clean') {
    return t('metadata.clean')
  }
  if (fixedAlbumImages.value[item.file]) {
    return t('metadata.fixed')
  }
  return item?.has_cover
    ? t('metadata.replaceAlbumCover')
    : t('metadata.missingImages')
}

function albumImageStatusBadgeClass(item) {
  if (
    activeAlbumImageTab.value === 'completed' ||
    fixedAlbumImages.value[item.file]
  ) {
    return 'badge-success text-success-content'
  }
  if (activeAlbumImageTab.value === 'clean') {
    return 'badge-soft'
  }
  return item?.has_cover
    ? 'badge-info text-info-content'
    : 'badge-warning text-warning-content'
}

function itemKey(item) {
  return `${item.artist_id || item.artist}-${item.folder}`
}

function jellyfinRepairKey(item) {
  return `${item.name || item.artist}-${item.folder || ''}-${item.file || ''}`
}

function jellyfinBucketItems(bucketKey) {
  const data = artistReconciliation.value || {}
  return data[bucketKey] || []
}

function isJellyfinRepairableItem(item) {
  return (
    item?.bucketKey !== 'tag_only' &&
    item?.missing_image &&
    (item?.file || item?.folder || item?.name) &&
    !fixedArtistImages.value[jellyfinRepairKey(item)]
  )
}

function isJellyfinTagRepairItem(item) {
  return (
    item?.bucketKey === 'tag_only' && !!item?.file && !fixed.value[item.file]
  )
}

function canUpdateJellyfinArtistImage(item) {
  return (
    !!item?.has_image &&
    !!(item?.folder || item?.file || item?.name) &&
    !isJellyfinRepairableItem(item)
  )
}

function artistImageActionItem(item) {
  const folder = String(item?.folder || item?.target || '').trim()
  const artist = folder || artistImageItemArtist(item)
  return {
    ...item,
    artist,
    name: artist,
    folder: folder || item?.folder || artist,
  }
}

function showArtistImageActionButton(item) {
  if (activeArtistImageTab.value === 'needs') {
    return true
  }
  if (isArtistImageUpdateTab.value) {
    return !!(item?.folder || item?.file || item?.artist)
  }
  if (activeArtistImageTab.value === 'failed') {
    return true
  }
  return false
}

function artistImageActionLabel(item) {
  const key = itemKey(item)
  if (applyingArtistImages.value[key]) {
    return t('metadata.fixing')
  }
  if (isArtistImageUpdateTab.value) {
    return t('metadata.updateCover')
  }
  if (activeArtistImageTab.value === 'failed') {
    return failedArtistRepairKeys.value[key]
      ? t('metadata.fixFailed')
      : t('metadata.chooseCover')
  }
  if (fixedArtistImages.value[key]) {
    return t('metadata.fixed')
  }
  if (failedArtistRepairKeys.value[key]) {
    return t('metadata.fixFailed')
  }
  return t('metadata.chooseCover')
}

function refreshArtistImageItemPreview(item, result) {
  const key = itemKey(item)
  const folder =
    result?.folder ||
    firstSavedFolder(result) ||
    item.folder ||
    item.target ||
    ''
  const preview_url = folder
    ? `${folderPreviewUrl(folder)}&t=${Date.now()}`
    : item.preview_url
  const updateList = (list) =>
    list.map((existing) =>
      itemKey(existing) === key
        ? { ...existing, ...result, preview_url }
        : existing
    )
  cleanArtistImageItems.value = updateList(cleanArtistImageItems.value)
  completedArtistImages.value = updateList(completedArtistImages.value)
  artistImageItems.value = updateList(artistImageItems.value)
  failedArtistImages.value = failedArtistImages.value.filter(
    (existing) => itemKey(existing) !== key
  )
}

function jellyfinRepairableBucketItems(bucketKey) {
  return jellyfinBucketItems(bucketKey).filter(isJellyfinRepairableItem)
}

function jellyfinTagRepairableBucketItems(bucketKey) {
  if (bucketKey !== 'tag_only') return []
  return jellyfinBucketItems(bucketKey).filter(
    (item) => item?.file && !fixed.value[item.file]
  )
}

function pendingArtistImageItems(items) {
  return (items || []).filter((item) => !fixedArtistImages.value[itemKey(item)])
}

function firstSavedFolder(result) {
  const path = [...(result?.verified || []), ...(result?.saved || [])].find(
    Boolean
  )
  return path ? String(path).split('/', 1)[0] : ''
}

async function invalidateRepairedArtistCover(item, result) {
  const artistName = String(
    result?.artist ||
      item?.artist ||
      item?.name ||
      result?.folder ||
      item?.folder ||
      firstSavedFolder(result) ||
      ''
  ).trim()
  if (!artistName) return
  await API.invalidateArtistCoverArt(artistName)
}

function folderPreviewUrl(folder) {
  const value = String(folder || '').trim()
  if (!value) return ''
  return `/api/metadata/artist-images/folder-preview?folder=${encodeURIComponent(
    value
  )}`
}

function enrichArtistImageItem(item) {
  if (!item || item.preview_url) {
    return item
  }
  const folder = item.folder || firstSavedFolder(item) || item.target || ''
  if (!folder) {
    return item
  }
  return {
    ...item,
    preview_url: folderPreviewUrl(folder),
  }
}

function artistImageRepairSucceeded(data) {
  return (
    data?.verified_on_disk === true &&
    [...(data?.verified || []), ...(data?.saved || [])].some(Boolean)
  )
}

function markArtistRepairFailed(key, error = '') {
  const nextFixed = { ...fixedArtistImages.value }
  delete nextFixed[key]
  fixedArtistImages.value = nextFixed
  failedArtistRepairKeys.value = {
    ...failedArtistRepairKeys.value,
    [key]: error || true,
  }
}

function markArtistRepairSucceeded(key) {
  const nextFailed = { ...failedArtistRepairKeys.value }
  delete nextFailed[key]
  failedArtistRepairKeys.value = nextFailed
  fixedArtistImages.value = {
    ...fixedArtistImages.value,
    [key]: true,
  }
}

function syncFailedRepairKeysFromReconciliation() {
  const stillMissing = new Set(
    (artistReconciliation.value?.missing_images || []).map((item) =>
      jellyfinRepairKey(item)
    )
  )
  const next = {}
  for (const [key, value] of Object.entries(failedArtistRepairKeys.value)) {
    if (stillMissing.has(key)) {
      next[key] = value
    }
  }
  failedArtistRepairKeys.value = next
}

function apiPreviewSrc(path) {
  return API.apiAssetUrl(path)
}

function artistImageItemArtist(item) {
  return (
    String(item?.artist || item?.name || '').trim() || t('common.unknownArtist')
  )
}

function artistImagePreviewUrl(item) {
  if (!item) return ''
  if (item.preview_url) {
    return apiPreviewSrc(item.preview_url)
  }
  const folder = item.folder || firstSavedFolder(item) || item.target || ''
  if (folder) {
    return apiPreviewSrc(
      `/api/metadata/artist-images/folder-preview?folder=${encodeURIComponent(
        folder
      )}`
    )
  }
  const file = String(item.file || '').trim()
  const artist = artistImageItemArtist(item)
  if (file && artist) {
    const artistId = String(item.artist_id || '').trim()
    const params = new URLSearchParams({
      file,
      artist,
      artist_id: artistId,
    })
    return apiPreviewSrc(`/api/metadata/artist-images/preview?${params}`)
  }
  return ''
}

function artistImageStatusBadge(item) {
  if (activeArtistImageTab.value === 'completed') {
    return t('metadata.completed')
  }
  if (activeArtistImageTab.value === 'clean') {
    return t('metadata.clean')
  }
  if (activeArtistImageTab.value === 'failed') {
    return failedArtistRepairKeys.value[itemKey(item)]
      ? t('metadata.fixFailed')
      : t('metadata.repairFailed')
  }
  if (fixedArtistImages.value[itemKey(item)]) {
    return t('metadata.fixed')
  }
  if (failedArtistRepairKeys.value[itemKey(item)]) {
    return t('metadata.fixFailed')
  }
  return t('metadata.needsFix')
}

function artistImageStatusBadgeClass(item) {
  if (activeArtistImageTab.value === 'failed') {
    return 'badge-error text-error-content'
  }
  if (
    activeArtistImageTab.value === 'needs' &&
    failedArtistRepairKeys.value[itemKey(item)]
  ) {
    return 'badge-error text-error-content'
  }
  if (
    activeArtistImageTab.value === 'completed' ||
    fixedArtistImages.value[itemKey(item)]
  ) {
    return 'badge-success text-success-content'
  }
  if (activeArtistImageTab.value === 'clean') {
    return 'badge-soft'
  }
  return 'badge-warning text-warning-content'
}

function isArtistImagePickerPreviewFailed(optionId) {
  return Boolean(artistImagePickerPreviewFailed.value[optionId])
}

function markArtistImagePickerPreviewFailed(optionId) {
  artistImagePickerPreviewFailed.value = {
    ...artistImagePickerPreviewFailed.value,
    [optionId]: true,
  }
}

function jellyfinPreviewSrc(item) {
  const key = jellyfinRepairKey(item)
  if (!item?.preview_url || jellyfinPreviewFailed.value[key]) {
    return ''
  }
  return apiPreviewSrc(item.preview_url)
}

function markJellyfinPreviewFailed(item) {
  const key = jellyfinRepairKey(item)
  jellyfinPreviewFailed.value = {
    ...jellyfinPreviewFailed.value,
    [key]: true,
  }
}

function jellyfinArtistName(item) {
  return String(item?.name || item?.artist || '').trim()
}

function sameJellyfinArtist(left, right) {
  return (
    jellyfinArtistName(left).toLocaleLowerCase() ===
    jellyfinArtistName(right).toLocaleLowerCase()
  )
}

function markJellyfinArtistImageFixed(item, result) {
  if (!artistImageRepairSucceeded(result)) {
    return
  }
  const folder = item.folder || result.folder || firstSavedFolder(result)
  const previewStamp = Date.now()
  const updateItem = (existing) => {
    if (!sameJellyfinArtist(existing, item)) return existing
    return {
      ...existing,
      folder: folder || existing.folder,
      has_image: true,
      missing_image: false,
      preview_url: folder
        ? `/api/metadata/artist-images/folder-preview?folder=${encodeURIComponent(
            folder
          )}&t=${previewStamp}`
        : existing.preview_url,
    }
  }
  const current = artistReconciliation.value || {}
  const counts = current.counts || {}
  artistReconciliation.value = {
    ...current,
    counts: {
      ...counts,
      missing_local_images: Math.max(0, (counts.missing_local_images || 0) - 1),
      local_images: (counts.local_images || 0) + 1,
    },
    matched: (current.matched || []).map(updateItem),
    folder_only: (current.folder_only || []).map(updateItem),
    jellyfin_only: (current.jellyfin_only || []).map(updateItem),
    tag_only: (current.tag_only || []).map(updateItem),
    missing_images: (current.missing_images || []).filter(
      (existing) => !sameJellyfinArtist(existing, item)
    ),
  }
}

function artistImageItemMeta(item) {
  if (activeArtistImageTab.value === 'completed') {
    const files = [...(item.saved || []), ...(item.verified || [])]
    return files.join(', ') || item.file || item.folder || ''
  }
  if (activeArtistImageTab.value === 'clean') {
    return item.file || item.folder || t('metadata.clean')
  }
  if (activeArtistImageTab.value === 'failed') {
    return item.file || item.target || item.folder || ''
  }
  return item.source || ''
}

function applyScanStatus(data) {
  loading.value = data.status === 'scanning'
  scanLimit.value = data.limit || scanLimit.value
  summary.value = {
    scanned: data.scanned || 0,
    matched: data.matched || 0,
    total: data.total || 0,
  }
  items.value = data.items || []
  cleanItems.value = data.clean || cleanItems.value
  completedItems.value = data.completed || completedItems.value
  if (data.status === 'error') {
    error.value = data.error || t('metadata.failedScan')
  }
}

function applyArtistImageStatus(data) {
  artistImageLoading.value = data.status === 'scanning'
  artistImageLimit.value = data.limit || artistImageLimit.value
  artistImageSummary.value = {
    scanned: data.scanned || 0,
    matched: data.matched || 0,
    total: data.total || 0,
  }
  artistImageItems.value = pendingArtistImageItems(data.items)
  artistImageSummary.value = {
    ...artistImageSummary.value,
    matched: artistImageItems.value.length,
  }
  cleanArtistImageItems.value = (data.clean || cleanArtistImageItems.value).map(
    enrichArtistImageItem
  )
  completedArtistImages.value = (
    data.completed || completedArtistImages.value
  ).map(enrichArtistImageItem)
  if (Array.isArray(data.failed) && data.failed.length > 0) {
    failedArtistImages.value = data.failed
  }
  if (data.status === 'error') {
    artistImageError.value = data.error || t('metadata.failedArtistImageScan')
  }
}

function applyAlbumImageStatus(data) {
  albumImageLoading.value = data.status === 'scanning'
  albumImageLimit.value = data.limit || albumImageLimit.value
  albumImageSummary.value = {
    scanned: data.scanned || 0,
    scannedAlbums: data.scanned_albums || data.scanned || 0,
    scannedTracks: data.scanned_tracks || 0,
    matched: data.matched || 0,
    total: data.total || 0,
    trackTotal: data.track_total || 0,
  }
  albumImageItems.value = data.items || []
  cleanAlbumImageItems.value = data.clean || cleanAlbumImageItems.value
  completedAlbumImages.value = data.completed || completedAlbumImages.value
  if (data.status === 'error') {
    albumImageError.value = data.error || t('metadata.failedAlbumImageScan')
  } else if (!repairingAllAlbumImages.value) {
    albumImageError.value = ''
  }
}

function albumImageRequestErrorMessage(err) {
  const detail = err?.response?.data?.detail
  if (detail) return detail
  const status = err?.response?.status
  const method = String(err?.config?.method || 'request').toUpperCase()
  const url = `${err?.config?.baseURL || ''}${err?.config?.url || ''}`
  if (status && url) {
    return `${t(
      'metadata.failedAlbumImageScan'
    )} ${method} ${url} returned ${status}.`
  }
  if (url) {
    return `${t('metadata.failedAlbumImageScan')} ${method} ${url}: ${
      err?.message || 'Network Error'
    }`
  }
  if (err?.message) {
    return `${t('metadata.failedAlbumImageScan')} ${err.message}`
  }
  return t('metadata.failedAlbumImageScan')
}

function applyArtistTagStatus(data) {
  artistTagLoading.value = data.status === 'scanning'
  artistTagLimit.value = data.limit || artistTagLimit.value
  artistTagSummary.value = {
    scanned: data.scanned || 0,
    matched: data.matched || 0,
    total: data.total || 0,
  }
  artistTagItems.value = data.items || []
  cleanArtistTagItems.value = data.clean || []
  completedArtistTags.value = data.completed || completedArtistTags.value
  if (data.status === 'error') {
    artistTagError.value = data.error || t('metadata.failedArtistTagScan')
  }
}

function stopPolling() {
  if (pollTimer !== null) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

function stopArtistImagePolling() {
  if (artistImagePollTimer !== null) {
    clearInterval(artistImagePollTimer)
    artistImagePollTimer = null
  }
}

function stopAlbumImagePolling() {
  if (albumImagePollTimer !== null) {
    clearInterval(albumImagePollTimer)
    albumImagePollTimer = null
  }
}

function stopArtistTagPolling() {
  if (artistTagPollTimer !== null) {
    clearInterval(artistTagPollTimer)
    artistTagPollTimer = null
  }
}

function startPolling() {
  stopPolling()
  pollTimer = setInterval(refreshScanStatus, 2000)
}

function startArtistImagePolling() {
  stopArtistImagePolling()
  artistImagePollTimer = setInterval(refreshArtistImageStatus, 1500)
}

function startAlbumImagePolling() {
  stopAlbumImagePolling()
  albumImagePollTimer = setInterval(refreshAlbumImageStatus, 1500)
}

function startArtistTagPolling() {
  stopArtistTagPolling()
  artistTagPollTimer = setInterval(refreshArtistTagStatus, 1500)
}

async function refreshScanStatus() {
  try {
    const res = await API.getMetadataScanStatus()
    applyScanStatus(res.data)
    if (res.data.status !== 'scanning') {
      stopPolling()
    }
  } catch {
    stopPolling()
    loading.value = false
    error.value = t('metadata.failedScan')
  }
}

async function refreshArtistImageStatus() {
  try {
    const res = await API.getArtistImageScanStatus()
    applyArtistImageStatus(res.data)
    if (res.data.status !== 'scanning') {
      stopArtistImagePolling()
    }
  } catch {
    stopArtistImagePolling()
    artistImageLoading.value = false
    artistImageError.value = t('metadata.failedArtistImageScan')
  }
}

async function refreshAlbumImageStatus() {
  try {
    const res = await API.getAlbumImageScanStatus()
    applyAlbumImageStatus(res.data)
    if (res.data.status !== 'scanning') {
      stopAlbumImagePolling()
      await loadAlbumImageLibrary()
    }
  } catch (err) {
    stopAlbumImagePolling()
    albumImageLoading.value = false
    albumImageError.value = albumImageRequestErrorMessage(err)
  }
}

async function refreshArtistTagStatus() {
  try {
    const res = await API.getArtistTagScanStatus()
    applyArtistTagStatus(res.data)
    if (res.data.status !== 'scanning') {
      stopArtistTagPolling()
    }
  } catch {
    stopArtistTagPolling()
    artistTagLoading.value = false
    artistTagError.value = t('metadata.failedArtistTagScan')
  }
}

async function scan() {
  loading.value = true
  error.value = ''
  fixed.value = {}
  try {
    const res = await API.startMetadataScan(scanLimit.value)
    applyScanStatus(res.data)
    if (res.data.status === 'scanning') {
      startPolling()
    }
  } catch {
    error.value = t('metadata.failedScan')
    loading.value = false
  }
}

async function scanAll() {
  loading.value = true
  error.value = ''
  fixed.value = {}
  try {
    const res = await API.startMetadataScan(scanLimit.value, true, true)
    applyScanStatus(res.data)
    if (res.data.status === 'scanning') {
      startPolling()
    }
  } catch {
    error.value = t('metadata.failedScan')
    loading.value = false
  }
}

async function scanArtistTags() {
  artistTagLoading.value = true
  artistTagError.value = ''
  fixedArtistTags.value = {}
  try {
    const res = await API.scanArtistTags(artistTagLimit.value)
    applyArtistTagStatus(res.data)
    if (res.data.status === 'scanning') {
      startArtistTagPolling()
    }
  } catch {
    artistTagError.value = t('metadata.failedArtistTagScan')
    artistTagLoading.value = false
  }
}

async function scanAllArtistTags() {
  artistTagLoading.value = true
  artistTagError.value = ''
  fixedArtistTags.value = {}
  try {
    const res = await API.scanArtistTags(artistTagLimit.value, true, true)
    applyArtistTagStatus(res.data)
    if (res.data.status === 'scanning') {
      startArtistTagPolling()
    }
  } catch {
    artistTagError.value = t('metadata.failedArtistTagScan')
    artistTagLoading.value = false
  }
}

async function reconcileArtists(options = {}) {
  const { preserveMessage = false } = options
  reconcilingArtists.value = true
  if (!preserveMessage) {
    jellyfinMessage.value = ''
    jellyfinError.value = false
  }
  try {
    const res = await API.reconcileJellyfinArtists()
    artistReconciliation.value = res.data
    jellyfinPreviewFailed.value = {}
    syncFailedRepairKeysFromReconciliation()
    lastReconciled.value = new Date().toLocaleString()
    if (!preserveMessage) {
      jellyfinMessage.value = t('metadata.jellyfinReconcileOk')
    }
  } catch (err) {
    jellyfinError.value = true
    jellyfinMessage.value =
      err?.response?.data?.detail || t('metadata.jellyfinRefreshFailed')
  } finally {
    reconcilingArtists.value = false
  }
}

async function refreshJellyfin() {
  refreshingJellyfin.value = true
  jellyfinMessage.value = ''
  jellyfinError.value = false
  try {
    await API.refreshJellyfinLibrary()
    jellyfinMessage.value = t('metadata.jellyfinRefreshOk')
  } catch (err) {
    jellyfinError.value = true
    jellyfinMessage.value =
      err?.response?.data?.detail || t('metadata.jellyfinRefreshFailed')
  } finally {
    refreshingJellyfin.value = false
  }
}

onMounted(async () => {
  syncMetadataMobileAction()
  await loadAlbumImageLibrary()
  try {
    const res = await API.getMetadataScanStatus()
    applyScanStatus(res.data)
    if (res.data.status === 'scanning') {
      startPolling()
    }
  } catch {
    // The page can still start a fresh scan if status lookup fails.
  }
  try {
    const res = await API.getArtistImageScanStatus()
    applyArtistImageStatus(res.data)
    if (res.data.status === 'scanning') {
      startArtistImagePolling()
    }
  } catch {
    // The page can still start a fresh artist image scan.
  }
  try {
    const res = await API.getAlbumImageScanStatus()
    applyAlbumImageStatus(res.data)
    if (res.data.status === 'scanning') {
      startAlbumImagePolling()
    }
  } catch {
    // The page can still start a fresh album image scan.
  }
  try {
    const res = await API.getArtistTagScanStatus()
    applyArtistTagStatus(res.data)
    if (res.data.status === 'scanning') {
      startArtistTagPolling()
    }
  } catch {
    // The page can still start a fresh artist repair scan.
  }
})

onBeforeUnmount(() => {
  clearMetadataMobileAction()
  stopPolling()
  stopArtistImagePolling()
  stopAlbumImagePolling()
  stopArtistTagPolling()
})

async function apply(item) {
  applying.value = { ...applying.value, [item.file]: true }
  error.value = ''
  try {
    const res = await API.applyMetadata(item.file, item.candidate || null)
    const remainingChanges = res.data?.changes || []
    if (remainingChanges.length === 0) {
      fixed.value = { ...fixed.value, [item.file]: true }
      completedItems.value = [res.data, ...completedItems.value]
      items.value = items.value.filter(
        (existing) => existing.file !== item.file
      )
      summary.value = {
        ...summary.value,
        matched: Math.max(0, summary.value.matched - 1),
      }
    } else {
      error.value = t('metadata.failedVerify')
    }
    if (remainingChanges.length > 0) {
      items.value = items.value.map((existing) =>
        existing.file === item.file
          ? {
              ...existing,
              current: res.data.current || existing.current,
              changes: remainingChanges,
            }
          : existing
      )
    }
  } catch (err) {
    const detail = err?.response?.data?.detail
    error.value = detail
      ? `${t('metadata.failedApply')} ${detail}`
      : t('metadata.failedApply')
  } finally {
    applying.value = { ...applying.value, [item.file]: false }
  }
}

async function repairAll() {
  repairingAll.value = true
  for (const item of [...items.value]) {
    // eslint-disable-next-line no-await-in-loop
    await apply(item)
  }
  repairingAll.value = false
}

async function applyArtistTagRepair(item, options = {}) {
  const { quiet = false } = options
  applyingArtistTags.value = {
    ...applyingArtistTags.value,
    [item.file]: true,
  }
  if (!quiet) artistTagError.value = ''
  try {
    const res = await API.applyArtistTags(
      item.file,
      item.candidate?.artists || []
    )
    const remainingChanges = res.data?.changes || []
    if (remainingChanges.length === 0) {
      fixedArtistTags.value = {
        ...fixedArtistTags.value,
        [item.file]: true,
      }
      completedArtistTags.value = [res.data, ...completedArtistTags.value]
      artistTagItems.value = artistTagItems.value.filter(
        (existing) => existing.file !== item.file
      )
      artistTagSummary.value = {
        ...artistTagSummary.value,
        matched: Math.max(0, artistTagSummary.value.matched - 1),
      }
      return true
    }
    artistTagItems.value = artistTagItems.value.map((existing) =>
      existing.file === item.file
        ? {
            ...existing,
            current: res.data.current || existing.current,
            changes: remainingChanges,
          }
        : existing
    )
    if (!quiet) artistTagError.value = t('metadata.failedVerify')
    return false
  } catch (err) {
    if (!quiet) {
      const detail = err?.response?.data?.detail
      artistTagError.value = detail
        ? `${t('metadata.failedArtistTagApply')} ${detail}`
        : t('metadata.failedArtistTagApply')
    }
    return false
  } finally {
    applyingArtistTags.value = {
      ...applyingArtistTags.value,
      [item.file]: false,
    }
  }
}

async function repairAllArtistTags() {
  const targets = [...artistTagItems.value]
  if (targets.length === 0) return
  repairingAllArtistTags.value = true
  artistTagError.value = ''
  let succeeded = 0
  let failed = 0
  try {
    for (const [index, item] of targets.entries()) {
      artistTagError.value = t('metadata.artistTagRepairProgressDetail')
        .replace('{current}', String(index + 1))
        .replace('{total}', String(targets.length))
        .replace('{name}', displaySong(item.current))
        .replace('{succeeded}', String(succeeded))
        .replace('{failed}', String(failed))
      // eslint-disable-next-line no-await-in-loop
      const ok = await applyArtistTagRepair(item, { quiet: true })
      if (ok) succeeded += 1
      else failed += 1
    }
    artistTagError.value =
      failed === 0
        ? t('metadata.artistTagRepairOk')
        : t('metadata.artistTagRepairPartial')
            .replace('{succeeded}', String(succeeded))
            .replace('{total}', String(targets.length))
  } finally {
    repairingAllArtistTags.value = false
  }
}

async function scanArtistImages() {
  artistImageLoading.value = true
  artistImageError.value = ''
  fixedArtistImages.value = {}
  failedArtistImages.value = []
  try {
    const res = await API.scanArtistImages(artistImageLimit.value)
    applyArtistImageStatus(res.data)
    if (res.data.status === 'scanning') {
      startArtistImagePolling()
    }
  } catch {
    artistImageError.value = t('metadata.failedArtistImageScan')
    artistImageLoading.value = false
  }
}

async function scanAllArtistImages() {
  artistImageLoading.value = true
  artistImageError.value = ''
  fixedArtistImages.value = {}
  failedArtistImages.value = []
  try {
    const res = await API.scanArtistImages(artistImageLimit.value, true, true)
    applyArtistImageStatus(res.data)
    if (res.data.status === 'scanning') {
      startArtistImagePolling()
    }
  } catch {
    artistImageError.value = t('metadata.failedArtistImageScan')
    artistImageLoading.value = false
  }
}

async function loadAlbumImageLibrary() {
  try {
    const res = await API.getLibraryFiles()
    albumImageLibraryItems.value = Array.isArray(res.data)
      ? res.data
      : Array.isArray(res.data?.items)
      ? res.data.items
      : []
  } catch {
    albumImageLibraryItems.value = []
  }
}

async function scanAlbumImages() {
  albumImageLoading.value = true
  albumImageError.value = ''
  fixedAlbumImages.value = {}
  try {
    const res = await API.scanAlbumImages(albumImageLimit.value)
    applyAlbumImageStatus(res.data)
    if (res.data.status === 'scanning') {
      startAlbumImagePolling()
    } else {
      await loadAlbumImageLibrary()
    }
  } catch (err) {
    albumImageError.value = albumImageRequestErrorMessage(err)
    albumImageLoading.value = false
  }
}

async function scanAllAlbumImages() {
  albumImageLoading.value = true
  albumImageError.value = ''
  fixedAlbumImages.value = {}
  try {
    const res = await API.scanAlbumImages(albumImageLimit.value, true, true)
    applyAlbumImageStatus(res.data)
    if (res.data.status === 'scanning') {
      startAlbumImagePolling()
    } else {
      await loadAlbumImageLibrary()
    }
  } catch (err) {
    albumImageError.value = albumImageRequestErrorMessage(err)
    albumImageLoading.value = false
  }
}

async function openAlbumImagePicker(item) {
  if (!item?.file) return
  artistImagePickerContext.value = 'album'
  artistImagePickerItem.value = item
  artistImagePickerOpen.value = true
  artistImagePickerOptions.value = []
  artistImagePickerSelected.value = null
  artistImagePickerError.value = ''
  artistImagePickerPreviewFailed.value = {}
  artistImagePickerLoading.value = true
  artistImagePickerSlowHint.value = false
  if (artistImagePickerSlowTimer !== null) {
    clearTimeout(artistImagePickerSlowTimer)
  }
  artistImagePickerSlowTimer = setTimeout(() => {
    artistImagePickerSlowHint.value = true
  }, 4000)
  try {
    const res = await API.getAlbumImageOptions(item.file, {
      album: item.album_name || item.name || item.current?.album_name || '',
      artist:
        item.artist ||
        item.current?.artist ||
        (item.artists || item.current?.artists || []).join(', '),
    })
    artistImagePickerOptions.value = res.data?.options || []
    if (artistImagePickerOptions.value.length === 1) {
      artistImagePickerSelected.value = artistImagePickerOptions.value[0]
    }
  } catch (err) {
    artistImagePickerError.value =
      err?.response?.data?.detail || t('metadata.chooseCoverFailed')
  } finally {
    artistImagePickerLoading.value = false
  }
}

async function applyAlbumImage(item, options = {}) {
  const { quiet = false, selection = null } = options
  const targetFiles =
    Array.isArray(item.files) && item.files.length ? item.files : [item.file]
  const applyKey = item.file
  applyingAlbumImages.value = {
    ...applyingAlbumImages.value,
    [applyKey]: true,
  }
  if (!quiet) albumImageError.value = ''
  try {
    const selectedCoverUrl =
      selection?.image_url || selection?.candidate?.cover_url || ''
    const candidate = selectedCoverUrl
      ? { cover_url: selectedCoverUrl }
      : item.candidate
    const res = await API.applyAlbumImage(item.file, candidate, targetFiles)
    if (!res.data?.has_cover) {
      if (!quiet) albumImageError.value = t('metadata.failedVerify')
      return false
    }
    const primaryResult = res.data
    fixedAlbumImages.value = {
      ...fixedAlbumImages.value,
      [applyKey]: true,
    }
    completedAlbumImages.value = [primaryResult, ...completedAlbumImages.value]
    albumImageItems.value = albumImageItems.value.filter(
      (existing) => !targetFiles.includes(existing.file)
    )
    albumImageSummary.value = {
      ...albumImageSummary.value,
      matched: albumImageItems.value.length,
    }
    API.clearCoverSourcesCache()
    await loadAlbumImageLibrary()
    return true
  } catch (err) {
    if (!quiet) {
      const detail = err?.response?.data?.detail
      albumImageError.value = detail
        ? `${t('metadata.failedAlbumImageApply')} ${detail}`
        : t('metadata.failedAlbumImageApply')
    }
    return false
  } finally {
    applyingAlbumImages.value = {
      ...applyingAlbumImages.value,
      [applyKey]: false,
    }
  }
}

async function repairAllAlbumImages() {
  const targets = [...albumImageItems.value]
  if (targets.length === 0) return
  repairingAllAlbumImages.value = true
  albumImageError.value = ''
  let succeeded = 0
  let failed = 0
  try {
    for (const [index, item] of targets.entries()) {
      albumImageError.value = t('metadata.albumImageRepairProgressDetail')
        .replace('{current}', String(index + 1))
        .replace('{total}', String(targets.length))
        .replace('{name}', displaySong(item.current))
        .replace('{succeeded}', String(succeeded))
        .replace('{failed}', String(failed))
      // eslint-disable-next-line no-await-in-loop
      const ok = await applyAlbumImage(item, { quiet: true })
      if (ok) succeeded += 1
      else failed += 1
    }
    albumImageError.value =
      failed === 0
        ? t('metadata.albumImageRepairOk')
        : t('metadata.albumImageRepairPartial')
            .replace('{succeeded}', String(succeeded))
            .replace('{total}', String(targets.length))
  } finally {
    repairingAllAlbumImages.value = false
  }
}

async function openArtistImagePicker(item, options = {}) {
  const { context = 'artist' } = options
  artistImagePickerContext.value = context
  artistImagePickerItem.value = item
  artistImagePickerOpen.value = true
  artistImagePickerOptions.value = []
  artistImagePickerSelected.value = null
  artistImagePickerError.value = ''
  artistImagePickerPreviewFailed.value = {}
  artistImagePickerLoading.value = true
  artistImagePickerSlowHint.value = false
  if (artistImagePickerSlowTimer !== null) {
    clearTimeout(artistImagePickerSlowTimer)
  }
  artistImagePickerSlowTimer = setTimeout(() => {
    artistImagePickerSlowHint.value = true
  }, 4000)
  try {
    const res = await API.getArtistImageOptions(item)
    artistImagePickerOptions.value = res.data?.options || []
    if (artistImagePickerOptions.value.length === 1) {
      artistImagePickerSelected.value = artistImagePickerOptions.value[0]
    }
  } catch (err) {
    artistImagePickerError.value =
      err?.response?.data?.detail || t('metadata.chooseCoverFailed')
  } finally {
    if (artistImagePickerSlowTimer !== null) {
      clearTimeout(artistImagePickerSlowTimer)
      artistImagePickerSlowTimer = null
    }
    artistImagePickerLoading.value = false
  }
}

function closeArtistImagePicker() {
  if (artistImagePickerApplying.value) return
  if (artistImagePickerSlowTimer !== null) {
    clearTimeout(artistImagePickerSlowTimer)
    artistImagePickerSlowTimer = null
  }
  artistImagePickerSlowHint.value = false
  artistImagePickerOpen.value = false
  artistImagePickerItem.value = null
  artistImagePickerOptions.value = []
  artistImagePickerSelected.value = null
  artistImagePickerError.value = ''
  artistImagePickerPreviewFailed.value = {}
}

async function confirmArtistImageSelection() {
  const item = artistImagePickerItem.value
  const selection = artistImagePickerSelected.value
  if (!item || !selection) return

  if (artistImagePickerContext.value === 'album') {
    closeArtistImagePicker()
    void applyAlbumImage(item, { selection })
    return
  }

  let ok = false
  artistImagePickerApplying.value = true
  try {
    if (artistImagePickerContext.value === 'jellyfin') {
      ok = await applyJellyfinArtistImage(item, {
        quiet: false,
        selection,
      })
    } else {
      ok = await applyArtistImageWithSelection(item, selection)
    }
  } finally {
    artistImagePickerApplying.value = false
    if (ok) {
      closeArtistImagePicker()
    }
  }
}

async function applyArtistImageWithSelection(item, selection = {}) {
  const key = itemKey(item)
  applyingArtistImages.value = {
    ...applyingArtistImages.value,
    [key]: true,
  }
  artistImageError.value = ''
  try {
    const res = await API.applyArtistImage(item, selection)
    if (!artistImageRepairSucceeded(res.data)) {
      markArtistRepairFailed(key, t('metadata.failedArtistImageApply'))
      artistImageError.value = t('metadata.failedArtistImageApply')
      return false
    }
    markArtistRepairSucceeded(key)
    await invalidateRepairedArtistCover(item, res.data)
    const completedItem = {
      ...res.data,
      preview_url: folderPreviewUrl(
        res.data?.folder || firstSavedFolder(res.data) || item.folder || ''
      ),
    }
    if (
      isArtistImageUpdateTab.value ||
      activeArtistImageTab.value === 'failed'
    ) {
      refreshArtistImageItemPreview(item, completedItem)
      artistImageError.value = ''
      return true
    }
    completedArtistImages.value = [
      completedItem,
      ...completedArtistImages.value,
    ]
    failedArtistImages.value = failedArtistImages.value.filter(
      (existing) => itemKey(existing) !== key
    )
    artistImageItems.value = artistImageItems.value.filter(
      (existing) => itemKey(existing) !== key
    )
    artistImageSummary.value = {
      ...artistImageSummary.value,
      matched: artistImageItems.value.length,
    }
    return true
  } catch (err) {
    const detail = err?.response?.data?.detail
    markArtistRepairFailed(key, detail || t('metadata.failedArtistImageApply'))
    artistImageError.value = detail
      ? `${t('metadata.failedArtistImageApply')} ${detail}`
      : t('metadata.failedArtistImageApply')
    failedArtistImages.value = [
      {
        ...item,
        error: detail || t('metadata.failedArtistImageApply'),
      },
      ...failedArtistImages.value.filter(
        (existing) => itemKey(existing) !== key
      ),
    ]
    return false
  } finally {
    applyingArtistImages.value = {
      ...applyingArtistImages.value,
      [key]: false,
    }
  }
}

async function applyJellyfinArtistImage(item, options = {}) {
  const { quiet = false, selection = null } = options
  const key = jellyfinRepairKey(item)
  applyingArtistImages.value = {
    ...applyingArtistImages.value,
    [key]: true,
  }
  if (!quiet) {
    jellyfinMessage.value = ''
    jellyfinError.value = false
  }
  try {
    const repairItem = {
      file: item.file || '',
      artist: item.name,
      artist_id: item.artist_id || '',
      folder: item.folder || item.name,
      jellyfin_artist_id:
        selection?.jellyfin_artist_id || item.jellyfin_artist_id || '',
    }
    const res = await API.applyArtistImage(repairItem, selection || {})
    if (!artistImageRepairSucceeded(res.data)) {
      throw new Error(t('metadata.failedArtistImageApply'))
    }
    markArtistRepairSucceeded(key)
    await invalidateRepairedArtistCover(item, res.data)
    const completedItem = {
      ...res.data,
      preview_url: folderPreviewUrl(
        res.data?.folder || firstSavedFolder(res.data) || item.folder || ''
      ),
    }
    completedArtistImages.value = [
      completedItem,
      ...completedArtistImages.value,
    ]
    markJellyfinArtistImageFixed(item, res.data)
    if (item.has_image) {
      const key = jellyfinRepairKey(item)
      const folder =
        item.folder || res.data?.folder || firstSavedFolder(res.data)
      if (folder) {
        const preview_url = `${folderPreviewUrl(folder)}&t=${Date.now()}`
        const updateBucket = (bucketKey) => {
          const data = artistReconciliation.value || {}
          const items = (data[bucketKey] || []).map((existing) =>
            jellyfinRepairKey(existing) === key
              ? {
                  ...existing,
                  preview_url,
                  has_image: true,
                  missing_image: false,
                }
              : existing
          )
          artistReconciliation.value = { ...data, [bucketKey]: items }
        }
        ;[
          'matched',
          'missing_images',
          'folder_only',
          'jellyfin_only',
          'tag_only',
        ].forEach(updateBucket)
        jellyfinPreviewFailed.value = { ...jellyfinPreviewFailed.value }
        delete jellyfinPreviewFailed.value[key]
      }
    }
    if (!quiet) {
      const sync = res.data?.jellyfin_sync
      if (sync && sync.synced === false) {
        jellyfinError.value = false
        jellyfinMessage.value = `${t('metadata.artistImageRepairOk')} ${t(
          'metadata.artistImageRepairSyncWarning'
        )}`
      } else {
        jellyfinMessage.value = t('metadata.artistImageRepairOk')
      }
    }
    return true
  } catch (err) {
    if (!quiet) {
      const detail =
        err?.response?.data?.detail ||
        err?.message ||
        t('metadata.failedArtistImageApply')
      markArtistRepairFailed(key, detail)
      jellyfinError.value = true
      jellyfinMessage.value = `${t(
        'metadata.failedArtistImageApply'
      )} ${detail}`
    } else {
      markArtistRepairFailed(key)
    }
    return false
  } finally {
    applyingArtistImages.value = {
      ...applyingArtistImages.value,
      [key]: false,
    }
  }
}

async function applyJellyfinMetadataRepair(item, options = {}) {
  const { quiet = false } = options
  if (!item?.file) return false
  applying.value = { ...applying.value, [item.file]: true }
  if (!quiet) {
    jellyfinMessage.value = ''
    jellyfinError.value = false
  }
  try {
    const res = await API.applyMetadata(item.file)
    const remainingChanges = res.data?.changes || []
    if (remainingChanges.length > 0) {
      throw new Error(t('metadata.failedVerify'))
    }
    fixed.value = { ...fixed.value, [item.file]: true }
    completedItems.value = [res.data, ...completedItems.value]
    if (!quiet) {
      jellyfinMessage.value = t('metadata.tagRepairOk')
      await reconcileArtists({ preserveMessage: true })
    }
    return true
  } catch (err) {
    if (!quiet) {
      const detail =
        err?.response?.data?.detail || err?.message || t('metadata.failedApply')
      jellyfinError.value = true
      jellyfinMessage.value = `${t('metadata.failedApply')} ${detail}`
    }
    return false
  } finally {
    applying.value = { ...applying.value, [item.file]: false }
  }
}

function finishJellyfinBulkRepair(succeeded, total, synced) {
  if (succeeded === 0) {
    jellyfinError.value = true
    jellyfinMessage.value = t('metadata.failedArtistImageApply')
    return
  }
  if (succeeded === total && synced) {
    jellyfinError.value = false
    jellyfinMessage.value = t('metadata.artistImageRepairOk')
    return
  }
  jellyfinError.value = succeeded < total
  jellyfinMessage.value = t('metadata.artistImageRepairPartial', {
    succeeded,
    total,
  })
}

async function runJellyfinBulkRepair(targets, bucketKey = '') {
  if (targets.length === 0) return

  jellyfinMessage.value = ''
  jellyfinError.value = false

  let succeeded = 0
  let failed = 0
  for (let index = 0; index < targets.length; index += 1) {
    const item = targets[index]
    jellyfinMessage.value = t('metadata.artistImageRepairProgressDetail', {
      current: index + 1,
      total: targets.length,
      name: item.name,
      succeeded,
      failed,
    })
    // eslint-disable-next-line no-await-in-loop
    const ok = await applyJellyfinArtistImage(item, { quiet: true })
    if (ok) succeeded += 1
    else failed += 1
  }

  const synced = await syncJellyfinAfterImageRepairs(succeeded)
  finishJellyfinBulkRepair(succeeded, targets.length, synced)
  if (succeeded > 0) {
    jellyfinMessage.value = t('metadata.artistImageRepairRefreshing')
    try {
      await reconcileArtists({ preserveMessage: true })
      finishJellyfinBulkRepair(succeeded, targets.length, synced)
    } catch {
      jellyfinError.value = true
      jellyfinMessage.value = t('metadata.jellyfinRepairSyncFailed')
    }
  }
  if (bucketKey) {
    repairingJellyfinBucket.value = ''
  } else {
    repairingAllJellyfin.value = false
  }
}

async function runJellyfinTagBulkRepair(targets) {
  if (targets.length === 0) return

  jellyfinMessage.value = ''
  jellyfinError.value = false

  let succeeded = 0
  let failed = 0
  for (let index = 0; index < targets.length; index += 1) {
    const item = targets[index]
    jellyfinMessage.value = t('metadata.tagRepairProgressDetail', {
      current: index + 1,
      total: targets.length,
      name: item.name,
      succeeded,
      failed,
    })
    // eslint-disable-next-line no-await-in-loop
    const ok = await applyJellyfinMetadataRepair(item, { quiet: true })
    if (ok) succeeded += 1
    else failed += 1
  }

  jellyfinError.value = succeeded === 0 || failed > 0
  jellyfinMessage.value =
    failed > 0
      ? t('metadata.tagRepairPartial', { succeeded, total: targets.length })
      : t('metadata.tagRepairOk')

  if (succeeded > 0) {
    try {
      await reconcileArtists({ preserveMessage: true })
    } catch {
      jellyfinError.value = true
      jellyfinMessage.value = t('metadata.jellyfinRepairSyncFailed')
    }
  }
}

async function repairAllArtistImages() {
  repairingAllImages.value = true
  for (const item of [...artistImageItems.value]) {
    // eslint-disable-next-line no-await-in-loop
    await applyArtistImageWithSelection(item, {})
  }
  repairingAllImages.value = false
}

async function repairAllJellyfinArtistImages() {
  const targets = [...allJellyfinRepairableItems.value]
  if (targets.length === 0) return

  repairingAllJellyfin.value = true
  await runJellyfinBulkRepair(targets)
}

async function repairJellyfinBucket(bucketKey) {
  if (bucketKey === 'tag_only') {
    const targets = [...jellyfinTagRepairableBucketItems(bucketKey)]
    if (targets.length === 0) return

    repairingJellyfinBucket.value = bucketKey
    try {
      await runJellyfinTagBulkRepair(targets)
    } finally {
      repairingJellyfinBucket.value = ''
    }
    return
  }

  const targets = [...jellyfinRepairableBucketItems(bucketKey)]
  if (targets.length === 0) return

  repairingJellyfinBucket.value = bucketKey
  await runJellyfinBulkRepair(targets, bucketKey)
}

async function syncJellyfinAfterImageRepairs(repairedCount) {
  if (repairedCount === 0) return false
  try {
    await API.refreshJellyfinLibrary()
    return true
  } catch (err) {
    const detail = err?.response?.data?.detail
    jellyfinError.value = true
    jellyfinMessage.value = detail
      ? `${t('metadata.jellyfinRepairSyncFailed')} ${detail}`
      : t('metadata.jellyfinRepairSyncFailed')
    return false
  }
}
</script>

<style scoped>
.metadata-section {
  @apply min-w-0 max-w-full;
}

.metadata-tab-shell {
  @apply mb-5 mx-auto flex w-full max-w-full min-w-0 gap-0.5 overflow-hidden rounded-full border border-white/10 bg-base-100/95 p-1 sm:mb-6 sm:w-max sm:gap-1;
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
}

[data-theme='downtify-light'] .metadata-tab-shell {
  @apply bg-white/95;
}

@media (max-width: 1023px) {
  .metadata-tool-tabs-mobile-menu {
    display: none;
  }
}

.metadata-tab-btn {
  @apply inline-flex min-w-0 flex-1 items-center justify-center whitespace-nowrap rounded-full px-1 py-2 font-medium transition-colors sm:flex-none sm:px-4 sm:text-sm;
  font-size: clamp(0.5rem, 2.45vw, 0.875rem);
}

.metadata-tab-btn > :deep(svg) {
  @apply mr-1 h-3 w-3 shrink-0 sm:mr-2 sm:h-4 sm:w-4;
}

.metadata-tab-badge {
  @apply ml-1 inline-flex min-w-[0.9rem] shrink items-center justify-center rounded-full px-1 py-0.5 text-[9px] font-bold leading-none sm:ml-2 sm:min-w-0 sm:px-2 sm:text-xs;
  background-color: color-mix(in srgb, currentColor 10%, transparent);
}

.metadata-album-image-results {
  scrollbar-width: none;
  -ms-overflow-style: none;
  -webkit-overflow-scrolling: touch;
}

.metadata-album-image-results::-webkit-scrollbar {
  display: none;
  width: 0;
  height: 0;
}

.metadata-album-artist-panel {
  @apply min-w-0 max-w-full overflow-hidden bg-base-100/95;
}

[data-theme='downtify-light'] .metadata-album-artist-panel {
  @apply bg-white/95;
}

.metadata-album-artist-scroll {
  @apply max-h-[34rem] min-h-0 overflow-x-hidden overflow-y-auto pr-1;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: thin;
}

@media (max-width: 639px) {
  .metadata-album-artist-scroll {
    max-height: min(31rem, calc(100dvh - 17rem));
  }
}

.metadata-album-artist-card {
  background-color: color-mix(in srgb, hsl(var(--b1)) 94%, transparent);
}

[data-theme='downtify-light'] .metadata-album-artist-card {
  @apply bg-white/95;
}

.metadata-mobile-menu-backdrop {
  @apply fixed inset-0 z-50 bg-black/30;
  padding-top: calc(var(--app-header-height) + var(--app-safe-top) + 0.5rem);
}

.metadata-mobile-menu {
  @apply ml-auto mr-3 flex w-64 max-w-[calc(100vw-1.5rem)] flex-col gap-1 rounded-2xl p-2 shadow-2xl;
}

.metadata-mobile-menu-item {
  @apply flex min-w-0 items-center gap-3 rounded-xl px-3 py-3 text-left text-sm font-medium text-base-content/70 transition-colors active:bg-white/10;
}

.metadata-mobile-menu-item-active {
  @apply bg-primary text-primary-content shadow-glow-sm;
}

.metadata-header {
  @apply mb-5 flex min-w-0 max-w-full flex-col gap-4 sm:flex-row sm:flex-wrap sm:items-end sm:justify-end;
}

.metadata-toolbar {
  @apply flex w-full min-w-0 max-w-full flex-col gap-2 sm:w-auto sm:flex-row sm:flex-wrap sm:items-center;
}

.metadata-btn {
  @apply h-auto min-h-10 max-w-full min-w-0 w-full rounded-full px-3 py-2 text-xs leading-snug sm:h-11 sm:w-auto sm:px-4 sm:text-sm sm:leading-normal;
  white-space: normal;
}

.metadata-btn.btn {
  flex-wrap: wrap;
  justify-content: center;
}

@media (min-width: 640px) {
  .metadata-btn {
    white-space: nowrap;
  }

  .metadata-btn.btn {
    flex-wrap: nowrap;
  }
}

.metadata-select {
  @apply select h-10 max-w-full min-w-0 w-full rounded-full border-white/10 bg-base-100/85 text-sm sm:h-11 sm:w-auto sm:min-w-[4.5rem];
}

.metadata-card-btn {
  @apply mt-3 h-auto min-h-9 max-w-full min-w-0 w-full rounded-full px-3 py-2 text-[0.7rem] leading-tight sm:h-8 sm:px-4 sm:text-xs sm:leading-normal;
  white-space: normal;
}

@media (min-width: 640px) {
  .metadata-card-btn {
    white-space: nowrap;
  }
}

.metadata-stat-grid {
  @apply mb-5 grid min-w-0 max-w-full grid-cols-3 gap-2 sm:gap-3;
}

.metadata-stat-card {
  @apply flex min-w-0 max-w-full w-full flex-col items-center justify-center p-2.5 text-center sm:items-start sm:p-4 sm:text-left;
}

.metadata-stat-label {
  @apply line-clamp-2 text-[10px] font-semibold uppercase leading-tight tracking-wide text-base-content/45 sm:text-xs;
}

.metadata-stat-value {
  @apply mt-1 text-lg font-semibold leading-none tabular-nums sm:mt-1.5 sm:text-2xl;
}

.metadata-stat-value-text {
  @apply normal-case leading-tight line-clamp-2 text-sm sm:text-lg;
  overflow-wrap: anywhere;
}

.metadata-stat-action {
  @apply mt-2 inline-flex h-auto min-h-9 w-auto max-w-full self-center items-center justify-center gap-1.5 rounded-full px-3 py-2 normal-case sm:mt-3 sm:self-start sm:gap-2 sm:px-4;
}

.metadata-stat-action-label {
  @apply text-[11px] font-semibold leading-none sm:text-xs;
}

.metadata-stat-grid-4 {
  @apply mb-5 grid min-w-0 max-w-full grid-cols-2 gap-2 sm:gap-3 lg:grid-cols-4;
}

.metadata-stat-grid > *,
.metadata-stat-grid-4 > * {
  @apply min-w-0 max-w-full;
}

.metadata-bucket-grid {
  @apply mb-4 grid min-w-0 max-w-full grid-cols-1 gap-3 min-[420px]:grid-cols-2 lg:grid-cols-4;
}

.metadata-bucket-btn {
  @apply min-w-0 max-w-full;
}

.metadata-artist-grid {
  @apply grid min-w-0 max-w-full grid-cols-1 gap-3 min-[400px]:grid-cols-2 md:grid-cols-3 xl:grid-cols-4;
}

.metadata-artist-grid > * {
  @apply min-w-0 max-w-full;
}

.metadata-bulk-bar {
  @apply mb-4 flex min-w-0 max-w-full flex-col gap-3 rounded-2xl border border-white/10 bg-base-100/60 p-3 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between;
}
</style>
