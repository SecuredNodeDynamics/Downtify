<template>
  <div class="min-h-0 overflow-x-hidden">
    <Navbar />

    <main class="mx-auto max-w-5xl overflow-x-hidden px-3 py-4 sm:px-6 sm:py-8">
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

      <div class="metadata-tab-shell tab-glow-shell">
        <button
          class="metadata-tab-btn"
          :class="
            activeToolTab === 'metadata'
              ? 'bg-primary text-primary-content shadow-glow-sm'
              : 'text-base-content/60 hover:text-base-content'
          "
          @click="activeToolTab = 'metadata'"
        >
          <Icon icon="clarity:tag-line" class="mr-2 inline h-4 w-4" />
          {{ t('metadata.metadataTab') }}
        </button>
        <button
          class="metadata-tab-btn"
          :class="
            activeToolTab === 'images'
              ? 'bg-primary text-primary-content shadow-glow-sm'
              : 'text-base-content/60 hover:text-base-content'
          "
          @click="activeToolTab = 'images'"
        >
          <Icon icon="clarity:image-gallery-line" class="mr-2 inline h-4 w-4" />
          {{ t('metadata.artistImagesTab') }}
        </button>
        <button
          class="metadata-tab-btn"
          :class="
            activeToolTab === 'artist-tags'
              ? 'bg-primary text-primary-content shadow-glow-sm'
              : 'text-base-content/60 hover:text-base-content'
          "
          @click="activeToolTab = 'artist-tags'"
        >
          <Icon icon="clarity:users-line" class="mr-2 inline h-4 w-4" />
          {{ t('metadata.artistRepairTab') }}
        </button>
        <button
          v-if="sm.settings.value.enable_jellyfin_tools"
          class="metadata-tab-btn"
          :class="
            activeToolTab === 'jellyfin'
              ? 'bg-primary text-primary-content shadow-glow-sm'
              : 'text-base-content/60 hover:text-base-content'
          "
          @click="activeToolTab = 'jellyfin'"
        >
          <Icon icon="clarity:server-line" class="mr-2 inline h-4 w-4" />
          {{ t('metadata.jellyfinTab') }}
        </button>
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
              <Icon
                v-else
                icon="clarity:image-gallery-line"
                class="h-4 w-4 mr-2"
              />
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
              icon="clarity:image-gallery-line"
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
                        : 'clarity:image-gallery-line'
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
                        ? 'clarity:image-gallery-line'
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

        <div class="max-h-[34rem] overflow-x-hidden overflow-y-auto pr-1 sm:pr-2">
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
                <div class="rounded-xl border border-white/10 bg-base-100/70 p-3">
                  <p class="text-[0.65rem] uppercase text-base-content/45">
                    {{ t('metadata.currentArtists') }}
                  </p>
                  <p class="mt-1 text-sm text-base-content/80">
                    {{ artistList(item.current?.artists) }}
                  </p>
                </div>
                <div class="rounded-xl border border-primary/20 bg-primary/10 p-3">
                  <p class="text-[0.65rem] uppercase text-primary/80">
                    {{ t('metadata.proposedArtists') }}
                  </p>
                  <p class="mt-1 text-sm text-primary">
                    {{ artistList(item.candidate?.artists) }}
                  </p>
                </div>
              </div>
              <button
                v-if="activeArtistTagTab === 'needs'"
                type="button"
                class="btn btn-sm metadata-card-btn mt-4 w-full border-white/10 bg-base-100/85 hover:bg-base-100"
                :class="fixedArtistTags[item.file] ? 'text-primary' : ''"
                :disabled="applyingArtistTags[item.file] || fixedArtistTags[item.file]"
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
              <Icon
                v-else
                icon="clarity:image-gallery-line"
                class="h-4 w-4 mr-2"
              />
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
                      icon="clarity:image-gallery-line"
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
                    <Icon
                      v-else
                      icon="clarity:tag-line"
                      class="h-4 w-4 mr-2"
                    />
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
                      icon="clarity:image-gallery-line"
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
            {{ t('metadata.chooseCoverTitle') }}
          </h3>
          <p class="mt-1 text-sm text-base-content/60">
            {{ artistImagePickerItem?.name || artistImagePickerItem?.artist }}
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
            {{ t('metadata.chooseCoverEmpty') }}
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
let artistTagPollTimer = null

const visibleItems = computed(() =>
  activeTab.value === 'completed'
    ? completedItems.value
    : activeTab.value === 'clean'
    ? cleanItems.value
    : items.value
)

const visibleArtistImageItems = computed(() =>
  activeArtistImageTab.value === 'completed'
    ? completedArtistImages.value
    : activeArtistImageTab.value === 'clean'
    ? cleanArtistImageItems.value
    : activeArtistImageTab.value === 'failed'
    ? failedArtistImages.value
    : artistImageItems.value
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

const reconciliationBuckets = computed(() => {
  const data = artistReconciliation.value || {}
  const buckets = [
    {
      key: 'missing_images',
      label: t('metadata.missingLocalImages'),
      items: data.missing_images || [],
      count: data.counts?.missing_local_images || 0,
      icon: 'clarity:image-gallery-line',
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
    item?.bucketKey === 'tag_only' &&
    !!item?.file &&
    !fixed.value[item.file]
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

function applyArtistTagStatus(data) {
  artistTagLoading.value = data.status === 'scanning'
  artistTagLimit.value = data.limit || artistTagLimit.value
  artistTagSummary.value = {
    scanned: data.scanned || 0,
    matched: data.matched || 0,
    total: data.total || 0,
  }
  artistTagItems.value = data.items || []
  cleanArtistTagItems.value = data.clean || cleanArtistTagItems.value
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
  stopPolling()
  stopArtistImagePolling()
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
        err?.response?.data?.detail ||
        err?.message ||
        t('metadata.failedApply')
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
  @apply mb-5 mx-auto flex w-max max-w-full min-w-0 gap-1 overflow-x-auto rounded-full border border-white/10 bg-base-100/75 p-1 sm:mb-6;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
}

.metadata-tab-shell::-webkit-scrollbar {
  display: none;
}

.metadata-tab-btn {
  @apply inline-flex max-w-full shrink-0 items-center justify-center whitespace-nowrap rounded-full px-3 py-2 text-sm font-medium transition-colors sm:px-4;
}

.metadata-tab-badge {
  @apply ml-1.5 inline-flex min-w-[1.1rem] shrink-0 items-center justify-center rounded-full px-1.5 py-0.5 text-[11px] font-bold leading-none sm:ml-2 sm:min-w-0 sm:px-2 sm:text-xs;
  background-color: color-mix(in srgb, currentColor 10%, transparent);
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
