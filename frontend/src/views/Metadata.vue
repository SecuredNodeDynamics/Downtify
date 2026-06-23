<template>
  <div class="min-h-screen overflow-x-hidden">
    <Navbar />
    <Settings />

    <main class="mx-auto max-w-5xl overflow-x-hidden px-3 py-6 sm:px-6 sm:py-8">
      <div class="mb-5">
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
          <div class="min-w-0">
            <h2 class="text-xl font-bold tracking-tight">
              {{ t('metadata.metadataTab') }}
            </h2>
            <p class="mt-1 text-sm text-base-content/60">
              {{ t('metadata.subtitle') }}
            </p>
          </div>
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
            {{ t('metadata.clean') }}
            <span
              class="ml-2 rounded-full bg-current/10 px-2 py-0.5 text-sm font-bold"
            >
              {{ cleanItems.length }}
            </span>
          </button>
        </div>

        <div class="max-h-[45rem] overflow-x-hidden overflow-y-auto pr-1 sm:pr-2">
          <div v-if="loading && visibleItems.length === 0" class="space-y-3">
            <div
              v-for="n in 5"
              :key="n"
              class="skeleton scan-skeleton-glow h-24 rounded-2xl"
            />
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

          <ul v-else class="space-y-3">
            <li
              v-for="item in visibleItems"
              :key="item.file"
              class="surface rounded-2xl p-4 transition-all duration-300"
              :class="
                applying[item.file]
                  ? 'max-md:scale-100 scale-[1.01] border-primary/40 shadow-glow-sm'
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
                  :class="
                    activeTab === 'completed'
                      ? 'badge-soft'
                      : activeTab === 'clean'
                        ? 'bg-white/5 text-base-content/50'
                        : 'bg-warning/10 text-warning'
                  "
                >
                  {{
                    activeTab === 'completed'
                      ? t('metadata.fixed')
                      : activeTab === 'clean'
                        ? t('metadata.clean')
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

              <div v-if="activeTab === 'needs'" class="mt-4 flex w-full sm:justify-end">
                <button
                  class="btn btn-sm metadata-btn h-10 border-white/10 bg-base-100/85 hover:bg-base-100"
                  :class="fixed[item.file] ? 'text-primary' : ''"
                  :disabled="applying[item.file] || fixed[item.file]"
                  @click="apply(item)"
                >
                  <span
                    v-if="applying[item.file]"
                    class="loading loading-spinner loading-xs mr-2"
                  />
                  <Icon v-else icon="clarity:check-line" class="h-4 w-4 mr-2" />
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
        </div>
      </section>

      <section v-if="activeToolTab === 'images'" class="metadata-section">
        <div class="metadata-header">
          <div class="min-w-0 flex-1">
            <h2 class="text-xl font-bold tracking-tight">
              {{ t('metadata.artistImages') }}
            </h2>
            <p class="mt-1 text-sm text-base-content/60">
              {{ t('metadata.artistImagesSubtitle') }}
            </p>
          </div>
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
          <div class="surface rounded-2xl p-4">
            <p class="text-xs uppercase text-base-content/40">
              {{ t('metadata.scanned') }}
            </p>
            <p class="mt-1 text-2xl font-semibold">
              {{ artistImageSummary.scanned }}
            </p>
          </div>
          <div class="surface rounded-2xl p-4">
            <p class="text-xs uppercase text-base-content/40">
              {{ t('metadata.missingImages') }}
            </p>
            <p class="mt-1 text-2xl font-semibold text-primary">
              {{ artistImageItems.length }}
            </p>
            <button
              class="btn btn-primary btn-xs metadata-card-btn"
              :disabled="artistImageItems.length === 0 || repairingAllImages"
              @click="repairAllArtistImages"
            >
              <span
                v-if="repairingAllImages"
                class="loading loading-spinner loading-xs mr-2"
              />
              <Icon
                v-else
                icon="clarity:magic-wand-line"
                class="h-4 w-4 mr-2"
              />
              {{ t('metadata.fixAllArtistImages') }}
            </button>
          </div>
          <div class="surface rounded-2xl p-4">
            <p class="text-xs uppercase text-base-content/40">
              {{ t('metadata.completed') }}
            </p>
            <p class="mt-1 text-2xl font-semibold">
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
            <span
              class="ml-2 rounded-full bg-current/10 px-2 py-0.5 text-sm font-bold"
            >
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
            <span
              class="ml-2 rounded-full bg-current/10 px-2 py-0.5 text-sm font-bold"
            >
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
            {{ t('metadata.clean') }}
            <span
              class="ml-2 rounded-full bg-current/10 px-2 py-0.5 text-sm font-bold"
            >
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
            {{ t('metadata.repairFailed') }}
            <span
              class="ml-2 rounded-full bg-current/10 px-2 py-0.5 text-sm font-bold"
            >
              {{ failedArtistImages.length }}
            </span>
          </button>
        </div>

        <div
          v-if="activeArtistImageTab === 'clean'"
          class="mb-5 flex justify-end"
        >
          <div
            class="inline-flex rounded-full border border-white/10 bg-base-100/75 p-1"
          >
            <button
              type="button"
              class="rounded-full p-2 transition-colors"
              :class="
                cleanArtistImageView === 'list'
                  ? 'bg-primary text-primary-content'
                  : 'text-base-content/55 hover:text-base-content'
              "
              :title="t('metadata.listView')"
              @click="cleanArtistImageView = 'list'"
            >
              <Icon icon="clarity:view-list-line" class="h-4 w-4" />
            </button>
            <button
              type="button"
              class="rounded-full p-2 transition-colors"
              :class="
                cleanArtistImageView === 'grid'
                  ? 'bg-primary text-primary-content'
                  : 'text-base-content/55 hover:text-base-content'
              "
              :title="t('metadata.gridView')"
              @click="cleanArtistImageView = 'grid'"
            >
              <Icon icon="clarity:grid-view-line" class="h-4 w-4" />
            </button>
          </div>
        </div>

        <div class="max-h-[34rem] overflow-x-hidden overflow-y-auto pr-1 sm:pr-2">
          <div
            v-if="artistImageLoading && visibleArtistImageItems.length === 0"
            class="space-y-3"
          >
            <div
              v-for="n in 4"
              :key="n"
              class="skeleton scan-skeleton-glow h-20 rounded-2xl"
            />
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

          <div
            v-else-if="
              activeArtistImageTab === 'clean' &&
              cleanArtistImageView === 'grid'
            "
            class="grid gap-4 grid-cols-1 min-[420px]:grid-cols-2 lg:grid-cols-3"
          >
            <article
              v-for="item in visibleArtistImageItems"
              :key="itemKey(item)"
              class="surface overflow-hidden rounded-2xl"
            >
              <div
                class="flex aspect-square items-center justify-center overflow-hidden bg-base-100/80"
              >
                <img
                  v-if="item.preview_url"
                  :src="item.preview_url"
                  :alt="item.artist"
                  class="h-full w-full object-cover"
                  loading="lazy"
                />
                <Icon
                  v-else
                  icon="clarity:user-line"
                  class="h-14 w-14 text-base-content/25"
                />
              </div>
              <div class="p-4">
                <div class="flex items-start justify-between gap-3">
                  <p class="min-w-0 truncate text-sm font-semibold">
                    {{ item.artist || t('common.unknownArtist') }}
                  </p>
                  <span class="pill badge-soft shrink-0">
                    {{ t('metadata.clean') }}
                  </span>
                </div>
                <p class="mt-2 truncate text-xs text-base-content/45">
                  {{ item.folder || item.file }}
                </p>
                <p class="mt-1 truncate text-xs text-primary">
                  {{ item.file }}
                </p>
              </div>
            </article>
          </div>

          <ul v-else class="space-y-3">
            <li
              v-for="item in visibleArtistImageItems"
              :key="itemKey(item)"
              class="surface rounded-2xl p-4"
              :class="
                applyingArtistImages[itemKey(item)]
                  ? 'max-md:scale-100 scale-[1.01] border-primary/40 shadow-glow-sm'
                  : ''
              "
            >
              <div class="metadata-artist-row">
                <div class="min-w-0">
                  <p class="truncate text-sm font-semibold">
                    {{ item.artist }}
                  </p>
                  <p class="mt-1 text-xs text-base-content/45">
                    {{ item.target || item.folder }}
                  </p>
                  <p class="mt-1 text-xs text-primary">
                    {{ artistImageItemMeta(item) }}
                  </p>
                  <p
                    v-if="activeArtistImageTab === 'failed'"
                    class="mt-2 text-xs text-error"
                  >
                    {{ item.error }}
                  </p>
                </div>
                <div
                  v-if="activeArtistImageTab === 'needs'"
                  class="metadata-preview-pair"
                >
                  <div>
                    <p
                      class="mb-1 text-center text-[0.65rem] uppercase text-base-content/40"
                    >
                      {{ t('metadata.before') }}
                    </p>
                    <div
                      class="flex aspect-square w-20 items-center justify-center rounded-xl border border-white/10 bg-base-100/80"
                    >
                      <Icon
                        icon="clarity:user-line"
                        class="h-9 w-9 text-base-content/35"
                      />
                    </div>
                  </div>
                  <div>
                    <p
                      class="mb-1 text-center text-[0.65rem] uppercase text-base-content/40"
                    >
                      {{ t('metadata.after') }}
                    </p>
                    <div
                      class="aspect-square w-20 overflow-hidden rounded-xl border border-primary/30 bg-base-100/80"
                    >
                      <img
                        v-if="item.preview_url"
                        :src="item.preview_url"
                        :alt="item.artist"
                        class="h-full w-full object-cover"
                        loading="lazy"
                      />
                      <div
                        v-else
                        class="flex h-full w-full items-center justify-center"
                      >
                        <Icon
                          icon="clarity:image-gallery-line"
                          class="h-9 w-9 text-base-content/35"
                        />
                      </div>
                    </div>
                  </div>
                </div>
                <button
                  v-if="activeArtistImageTab === 'needs'"
                  class="btn btn-sm metadata-btn h-10 w-full border-white/10 bg-base-100/85 hover:bg-base-100 md:w-auto"
                  :class="
                    fixedArtistImages[itemKey(item)] ? 'text-primary' : ''
                  "
                  :disabled="
                    applyingArtistImages[itemKey(item)] ||
                    fixedArtistImages[itemKey(item)]
                  "
                  @click="applyArtistImage(item)"
                >
                  <span
                    v-if="applyingArtistImages[itemKey(item)]"
                    class="loading loading-spinner loading-xs mr-2"
                  />
                  <Icon v-else icon="clarity:check-line" class="h-4 w-4 mr-2" />
                  {{
                    applyingArtistImages[itemKey(item)]
                      ? t('metadata.fixing')
                      : fixedArtistImages[itemKey(item)]
                        ? t('metadata.fixed')
                        : t('metadata.apply')
                  }}
                </button>
              </div>
            </li>
          </ul>
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
          <div class="min-w-0 flex-1">
            <h2 class="text-xl font-bold tracking-tight">
              {{ t('metadata.jellyfinTools') }}
            </h2>
            <p class="mt-1 text-sm text-base-content/60">
              {{ t('metadata.jellyfinToolsSubtitle') }}
            </p>
          </div>
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
          <div class="surface rounded-2xl p-4">
            <p class="text-xs uppercase text-base-content/40">
              {{ t('metadata.jellyfinLibrary') }}
            </p>
            <p class="mt-1 truncate text-lg font-semibold">
              {{ jellyfinLibraryName }}
            </p>
            <button
              class="btn btn-primary btn-xs metadata-card-btn"
              :disabled="refreshingJellyfin || reconcilingArtists"
              @click="refreshJellyfin"
            >
              <span
                v-if="refreshingJellyfin"
                class="loading loading-spinner loading-xs mr-2"
              />
              <Icon v-else icon="clarity:sync-line" class="h-4 w-4 mr-2" />
              {{ t('metadata.refreshJellyfin') }}
            </button>
          </div>
          <div class="surface rounded-2xl p-4">
            <p class="text-xs uppercase text-base-content/40">
              {{ t('metadata.jellyfinArtists') }}
            </p>
            <p class="mt-1 text-2xl font-semibold text-primary">
              {{ jellyfinCounts.jellyfin }}
            </p>
            <p class="mt-3 text-[11px] leading-snug text-base-content/45">
              {{
                t('metadata.bulkFixAvailable', {
                  count: jellyfinRepairableBucketItems('missing_images').length,
                })
              }}
            </p>
          </div>
          <div class="surface rounded-2xl p-4">
            <p class="text-xs uppercase text-base-content/40">
              {{ t('metadata.localArtistFolders') }}
            </p>
            <p class="mt-1 text-2xl font-semibold">
              {{ jellyfinCounts.folders }}
            </p>
            <button
              class="btn btn-primary btn-xs metadata-card-btn"
              :disabled="
                repairingJellyfinBucket === 'folder_only' ||
                repairingAllJellyfin ||
                reconcilingArtists ||
                jellyfinRepairableBucketItems('folder_only').length === 0
              "
              @click="repairJellyfinBucket('folder_only')"
            >
              <span
                v-if="repairingJellyfinBucket === 'folder_only'"
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
          <div class="surface rounded-2xl p-4">
            <p class="text-xs uppercase text-base-content/40">
              {{ t('metadata.missingLocalImages') }}
            </p>
            <p class="mt-1 text-2xl font-semibold text-primary">
              {{ jellyfinCounts.missingImages }}
            </p>
            <button
              class="btn btn-primary btn-xs metadata-card-btn"
              :disabled="
                repairingJellyfinBucket === 'missing_images' ||
                repairingAllJellyfin ||
                reconcilingArtists ||
                jellyfinRepairableBucketItems('missing_images').length === 0
              "
              @click="repairJellyfinBucket('missing_images')"
            >
              <span
                v-if="repairingJellyfinBucket === 'missing_images'"
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

        <div v-else-if="artistReconciliation" class="surface min-w-0 rounded-2xl p-3 sm:p-4">
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

          <div
            v-if="activeReconciliationBucketMeta"
            class="metadata-bulk-bar"
          >
            <div class="min-w-0">
              <p class="text-sm font-semibold">
                {{ activeReconciliationBucketMeta.label }}
              </p>
              <p class="text-xs text-base-content/45">
                {{
                  t('metadata.bulkFixReady', {
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
                    v-if="item.preview_url"
                    :src="item.preview_url"
                    :alt="item.name"
                    class="h-full w-full object-cover"
                    loading="lazy"
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
                    <span class="loading loading-spinner loading-md text-primary" />
                    <p class="text-[11px] font-medium text-base-content/70">
                      {{ t('metadata.fixing') }}
                    </p>
                  </div>
                </div>
                <div class="p-3">
                  <p class="truncate text-sm font-semibold">
                    {{ item.name }}
                  </p>
                  <div class="mt-2 flex items-center gap-2">
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
                    v-if="isJellyfinRepairableItem(item)"
                    class="btn btn-primary btn-xs metadata-card-btn"
                    :disabled="
                      applyingArtistImages[jellyfinRepairKey(item)] ||
                      fixedArtistImages[jellyfinRepairKey(item)]
                    "
                    @click="applyJellyfinArtistImage(item)"
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
                        : t('metadata.applyImage')
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
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { Icon } from '@iconify/vue'

import Navbar from '/src/components/Navbar.vue'
import Settings from '/src/components/Settings.vue'
import API from '/src/model/api'
import { useSettingsManager } from '/src/model/settings'
import { useI18n } from '/src/i18n'

const { t } = useI18n()
const sm = useSettingsManager()
const JELLYFIN_IMAGE_REPAIR_BUCKETS = [
  'missing_images',
  'jellyfin_only',
  'folder_only',
  'tag_only',
]
const activeToolTab = ref('metadata')
const loading = ref(false)
const error = ref('')
const items = ref([])
const cleanItems = ref([])
const applying = ref({})
const fixed = ref({})
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
const cleanArtistImageView = ref('grid')
const applyingArtistImages = ref({})
const fixedArtistImages = ref({})
const repairingAllImages = ref(false)
const artistImageSummary = ref({ scanned: 0, matched: 0, total: 0 })
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
    repairableCount: jellyfinRepairableBucketItems(bucket.key).length,
  }))
})

const reconciliationGridItems = computed(() =>
  reconciliationBuckets.value
    .filter((bucket) => bucket.key === activeReconciliationBucket.value)
    .flatMap((bucket) =>
      (bucket.items || [])
        .filter((item) => item.missing_image)
        .map((item) => ({
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
    item?.missing_image &&
    (item?.file || item?.folder || item?.name) &&
    !fixedArtistImages.value[jellyfinRepairKey(item)]
  )
}

function jellyfinRepairableBucketItems(bucketKey) {
  return jellyfinBucketItems(bucketKey).filter(isJellyfinRepairableItem)
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

function jellyfinArtistName(item) {
  return String(item?.name || item?.artist || '').trim()
}

function sameJellyfinArtist(left, right) {
  return (
    jellyfinArtistName(left).casefold() === jellyfinArtistName(right).casefold()
  )
}

function markJellyfinArtistImageFixed(item, result) {
  const folder = item.folder || firstSavedFolder(result)
  const previewStamp = Date.now()
  const updateItem = (existing) => {
    if (!sameJellyfinArtist(existing, item)) return existing
    return {
      ...existing,
      folder: folder || existing.folder,
      has_image: true,
      missing_image: false,
      preview_url: folder
        ? `/api/metadata/artist-images/folder-preview?folder=${encodeURIComponent(folder)}&t=${previewStamp}`
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
      (existing) => !sameJellyfinArtist(existing, item),
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
  cleanArtistImageItems.value = data.clean || cleanArtistImageItems.value
  completedArtistImages.value = data.completed || completedArtistImages.value
  if (Array.isArray(data.failed) && data.failed.length > 0) {
    failedArtistImages.value = data.failed
  }
  if (data.status === 'error') {
    artistImageError.value = data.error || t('metadata.failedArtistImageScan')
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

function startPolling() {
  stopPolling()
  pollTimer = setInterval(refreshScanStatus, 2000)
}

function startArtistImagePolling() {
  stopArtistImagePolling()
  artistImagePollTimer = setInterval(refreshArtistImageStatus, 1500)
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
})

onBeforeUnmount(() => {
  stopPolling()
  stopArtistImagePolling()
})

async function apply(item) {
  applying.value = { ...applying.value, [item.file]: true }
  error.value = ''
  try {
    const res = await API.applyMetadata(item.file)
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

async function applyArtistImage(item) {
  const key = itemKey(item)
  applyingArtistImages.value = {
    ...applyingArtistImages.value,
    [key]: true,
  }
  artistImageError.value = ''
  try {
    const res = await API.applyArtistImage(item)
    const savedOrVerified = [
      ...(res.data?.saved || []),
      ...(res.data?.verified || []),
    ]
    if (savedOrVerified.length === 0) {
      artistImageError.value = t('metadata.failedArtistImageApply')
      return
    }
    fixedArtistImages.value = { ...fixedArtistImages.value, [key]: true }
    completedArtistImages.value = [res.data, ...completedArtistImages.value]
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
  } catch (err) {
    const detail = err?.response?.data?.detail
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
  } finally {
    applyingArtistImages.value = {
      ...applyingArtistImages.value,
      [key]: false,
    }
  }
}

async function applyJellyfinArtistImage(item, options = {}) {
  const { quiet = false } = options
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
    }
    const res = await API.applyArtistImage(repairItem)
    const savedOrVerified = [
      ...(res.data?.saved || []),
      ...(res.data?.verified || []),
    ]
    if (savedOrVerified.length === 0) {
      throw new Error(t('metadata.failedArtistImageApply'))
    }
    fixedArtistImages.value = { ...fixedArtistImages.value, [key]: true }
    completedArtistImages.value = [res.data, ...completedArtistImages.value]
    markJellyfinArtistImageFixed(item, res.data)
    if (!quiet) {
      const sync = res.data?.jellyfin_sync
      if (sync && sync.synced === false) {
        jellyfinError.value = false
        jellyfinMessage.value = `${t('metadata.artistImageRepairOk')} ${t('metadata.artistImageRepairSyncWarning')}`
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
      jellyfinError.value = true
      jellyfinMessage.value = `${t('metadata.failedArtistImageApply')} ${detail}`
    }
    return false
  } finally {
    applyingArtistImages.value = {
      ...applyingArtistImages.value,
      [key]: false,
    }
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

async function repairAllArtistImages() {
  repairingAllImages.value = true
  for (const item of [...artistImageItems.value]) {
    // eslint-disable-next-line no-await-in-loop
    await applyArtistImage(item)
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
  @apply mb-5 flex w-full max-w-full min-w-0 gap-1 overflow-x-auto rounded-2xl border bg-base-100/75 p-1 sm:mb-6 sm:inline-flex sm:w-auto sm:overflow-visible sm:rounded-full;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
}

.metadata-tab-shell::-webkit-scrollbar {
  display: none;
}

.metadata-tab-btn {
  @apply max-w-full shrink-0 whitespace-nowrap rounded-full px-3 py-2 text-sm font-medium transition-colors sm:px-4;
}

.metadata-header {
  @apply mb-5 flex min-w-0 max-w-full flex-col gap-4 sm:flex-row sm:flex-wrap sm:items-end sm:justify-between;
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
  @apply mb-5 grid min-w-0 max-w-full grid-cols-1 gap-3 min-[420px]:grid-cols-2 sm:grid-cols-3;
}

.metadata-stat-grid-4 {
  @apply mb-5 grid min-w-0 max-w-full grid-cols-1 gap-3 min-[420px]:grid-cols-2 xl:grid-cols-4;
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

.metadata-artist-row {
  @apply flex min-w-0 max-w-full flex-col gap-4 md:grid md:grid-cols-[minmax(0,1fr)_auto_auto] md:items-center;
}

.metadata-preview-pair {
  @apply mx-auto grid w-full min-w-0 max-w-[11rem] grid-cols-2 items-center gap-2 sm:gap-3 md:mx-0 md:justify-self-center;
}

.metadata-bulk-bar {
  @apply mb-4 flex min-w-0 max-w-full flex-col gap-3 rounded-2xl border border-white/10 bg-base-100/60 p-3 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between;
}
</style>
