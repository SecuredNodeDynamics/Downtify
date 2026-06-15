<template>
  <div class="min-h-screen">
    <Navbar />
    <Settings />

    <main class="mx-auto max-w-5xl px-4 py-8 sm:px-6">
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

      <div
        class="tab-glow-shell mb-6 inline-flex rounded-full border bg-base-100/75 p-1"
      >
        <button
          class="rounded-full px-4 py-2 text-sm font-medium transition-colors"
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
          class="rounded-full px-4 py-2 text-sm font-medium transition-colors"
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
          class="rounded-full px-4 py-2 text-sm font-medium transition-colors"
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

      <section v-if="activeToolTab === 'metadata'">
        <div class="mb-5 flex flex-wrap items-end justify-between gap-4">
          <div>
            <h2 class="text-xl font-bold tracking-tight">
              {{ t('metadata.metadataTab') }}
            </h2>
            <p class="mt-1 text-sm text-base-content/60">
              {{ t('metadata.subtitle') }}
            </p>
          </div>
        <div class="flex items-center gap-2">
          <select
            v-model.number="scanLimit"
            class="select h-11 rounded-full border-white/10 bg-base-100/85 text-sm"
            :disabled="loading"
            :title="t('metadata.resultLimit')"
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
          <button
            class="btn btn-sm h-11 rounded-full border-white/10 bg-base-100/85 hover:bg-base-100"
            :disabled="loading"
            @click="scanAll"
          >
            <Icon icon="clarity:fast-forward-line" class="h-4 w-4 mr-2" />
            {{ t('metadata.scanAll') }}
          </button>
          <button
            class="btn btn-sm h-11 rounded-full border-white/10 bg-base-100/85 hover:bg-base-100"
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
            <Icon v-else icon="clarity:check-circle-line" class="h-4 w-4 mr-2" />
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

      <div
        class="tab-glow-shell mb-5 inline-flex rounded-full border bg-base-100/75 p-1"
      >
        <button
          class="rounded-full px-4 py-2 text-sm font-medium transition-colors"
          :class="
            activeTab === 'needs'
              ? 'bg-primary text-primary-content shadow-glow-sm'
              : 'text-base-content/60 hover:text-base-content'
          "
          @click="activeTab = 'needs'"
        >
          {{ t('metadata.needsFix') }}
          <span class="ml-2 rounded-full bg-current/10 px-2 py-0.5 text-sm font-bold">
            {{ items.length }}
          </span>
        </button>
        <button
          class="rounded-full px-4 py-2 text-sm font-medium transition-colors"
          :class="
            activeTab === 'completed'
              ? 'bg-primary text-primary-content shadow-glow-sm'
              : 'text-base-content/60 hover:text-base-content'
          "
          @click="activeTab = 'completed'"
        >
          {{ t('metadata.completed') }}
          <span class="ml-2 rounded-full bg-current/10 px-2 py-0.5 text-sm font-bold">
            {{ completedItems.length }}
          </span>
        </button>
        <button
          class="rounded-full px-4 py-2 text-sm font-medium transition-colors"
          :class="
            activeTab === 'clean'
              ? 'bg-primary text-primary-content shadow-glow-sm'
              : 'text-base-content/60 hover:text-base-content'
          "
          @click="activeTab = 'clean'"
        >
          {{ t('metadata.clean') }}
          <span class="ml-2 rounded-full bg-current/10 px-2 py-0.5 text-sm font-bold">
            {{ cleanItems.length }}
          </span>
        </button>
      </div>

      <div class="max-h-[45rem] overflow-y-auto pr-2">
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

            <div v-if="activeTab === 'needs'" class="mt-4 flex justify-end">
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
      </div>

      </section>

      <section v-if="activeToolTab === 'images'">
        <div class="mb-5 flex flex-wrap items-end justify-between gap-4">
          <div class="min-w-0 flex-1">
            <h2 class="text-xl font-bold tracking-tight">
              {{ t('metadata.artistImages') }}
            </h2>
            <p class="mt-1 text-sm text-base-content/60">
              {{ t('metadata.artistImagesSubtitle') }}
            </p>
          </div>
          <div class="flex shrink-0 items-center gap-2">
            <select
              v-model.number="artistImageLimit"
              class="select h-11 rounded-full border-white/10 bg-base-100/85 text-sm"
              :disabled="artistImageLoading"
              :title="t('metadata.artistImageLimit')"
            >
              <option :value="25">25</option>
              <option :value="50">50</option>
              <option :value="100">100</option>
            </select>
            <button
              class="btn btn-primary btn-sm h-11 rounded-full px-5"
              :disabled="artistImageLoading"
              @click="scanArtistImages"
            >
              <span
                v-if="artistImageLoading"
                class="loading loading-spinner loading-xs mr-2"
              />
              <Icon v-else icon="clarity:image-gallery-line" class="h-4 w-4 mr-2" />
              {{ t('metadata.scanArtistImages') }}
            </button>
            <button
              class="btn btn-sm h-11 rounded-full border-white/10 bg-base-100/85 hover:bg-base-100"
              :disabled="artistImageLoading"
              @click="scanAllArtistImages"
            >
              <Icon icon="clarity:fast-forward-line" class="h-4 w-4 mr-2" />
              {{ t('metadata.scanAll') }}
            </button>
            <button
              class="btn btn-sm h-11 rounded-full border-white/10 bg-base-100/85 hover:bg-base-100"
              :disabled="
                activeArtistImageTab !== 'needs' ||
                artistImageItems.length === 0 ||
                repairingAllImages
              "
              @click="repairAllArtistImages"
            >
              <span
                v-if="repairingAllImages"
                class="loading loading-spinner loading-xs mr-2"
              />
              <Icon v-else icon="clarity:check-circle-line" class="h-4 w-4 mr-2" />
              {{ t('metadata.repairAll') }}
            </button>
          </div>
        </div>

        <div
          v-if="artistImageError"
          class="surface mb-4 flex items-center gap-3 rounded-2xl p-4 text-sm text-error"
        >
          <Icon icon="clarity:exclamation-circle-line" class="h-5 w-5" />
          <span>{{ artistImageError }}</span>
        </div>

        <section class="mb-5 grid gap-3 sm:grid-cols-3">
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

        <div
          class="tab-glow-shell mb-5 inline-flex rounded-full border bg-base-100/75 p-1"
        >
          <button
            class="rounded-full px-4 py-2 text-sm font-medium transition-colors"
            :class="
              activeArtistImageTab === 'needs'
                ? 'bg-primary text-primary-content shadow-glow-sm'
                : 'text-base-content/60 hover:text-base-content'
            "
            @click="activeArtistImageTab = 'needs'"
          >
            {{ t('metadata.needsFix') }}
            <span class="ml-2 rounded-full bg-current/10 px-2 py-0.5 text-sm font-bold">
              {{ artistImageItems.length }}
            </span>
          </button>
          <button
            class="rounded-full px-4 py-2 text-sm font-medium transition-colors"
            :class="
              activeArtistImageTab === 'completed'
                ? 'bg-primary text-primary-content shadow-glow-sm'
                : 'text-base-content/60 hover:text-base-content'
            "
            @click="activeArtistImageTab = 'completed'"
          >
            {{ t('metadata.completed') }}
            <span class="ml-2 rounded-full bg-current/10 px-2 py-0.5 text-sm font-bold">
              {{ completedArtistImages.length }}
            </span>
          </button>
          <button
            class="rounded-full px-4 py-2 text-sm font-medium transition-colors"
            :class="
              activeArtistImageTab === 'clean'
                ? 'bg-primary text-primary-content shadow-glow-sm'
                : 'text-base-content/60 hover:text-base-content'
            "
            @click="activeArtistImageTab = 'clean'"
          >
            {{ t('metadata.clean') }}
            <span class="ml-2 rounded-full bg-current/10 px-2 py-0.5 text-sm font-bold">
              {{ cleanArtistImageItems.length }}
            </span>
          </button>
          <button
            class="rounded-full px-4 py-2 text-sm font-medium transition-colors"
            :class="
              activeArtistImageTab === 'failed'
                ? 'bg-primary text-primary-content shadow-glow-sm'
                : 'text-base-content/60 hover:text-base-content'
            "
            @click="activeArtistImageTab = 'failed'"
          >
            {{ t('metadata.repairFailed') }}
            <span class="ml-2 rounded-full bg-current/10 px-2 py-0.5 text-sm font-bold">
              {{ failedArtistImages.length }}
            </span>
          </button>
        </div>

        <div class="max-h-[34rem] overflow-y-auto pr-2">
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

          <ul v-else class="space-y-3">
            <li
              v-for="item in visibleArtistImageItems"
              :key="itemKey(item)"
              class="surface rounded-2xl p-4"
              :class="
                applyingArtistImages[itemKey(item)]
                  ? 'scale-[1.01] border-primary/40 shadow-glow-sm'
                  : ''
              "
            >
              <div class="grid gap-4 md:grid-cols-[minmax(0,1fr)_auto_auto] md:items-center">
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
                  class="grid grid-cols-[5rem_5rem] items-center gap-3 justify-self-center"
                >
                  <div>
                    <p class="mb-1 text-center text-[0.65rem] uppercase text-base-content/40">
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
                    <p class="mb-1 text-center text-[0.65rem] uppercase text-base-content/40">
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
                  class="btn btn-sm h-10 rounded-full border-white/10 bg-base-100/85 hover:bg-base-100"
                  :class="fixedArtistImages[itemKey(item)] ? 'text-primary' : ''"
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
      >
        <div class="mb-5 flex flex-wrap items-end justify-between gap-4">
          <div class="min-w-0 flex-1">
            <h2 class="text-xl font-bold tracking-tight">
              {{ t('metadata.jellyfinTools') }}
            </h2>
            <p class="mt-1 text-sm text-base-content/60">
              {{ t('metadata.jellyfinToolsSubtitle') }}
            </p>
          </div>
          <div class="flex shrink-0 flex-wrap items-center gap-2">
            <button
              class="btn btn-primary btn-sm h-11 rounded-full px-5"
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
              class="btn btn-sm h-11 rounded-full border-white/10 bg-base-100/85 hover:bg-base-100"
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
          </div>
        </div>

        <div class="mb-5 grid gap-3 sm:grid-cols-3">
          <div class="surface rounded-2xl p-4">
            <p class="text-xs uppercase text-base-content/40">
              {{ t('metadata.jellyfinLibrary') }}
            </p>
            <p class="mt-1 truncate text-lg font-semibold">
              {{ jellyfinLibraryName }}
            </p>
          </div>
          <div class="surface rounded-2xl p-4">
            <p class="text-xs uppercase text-base-content/40">
              {{ t('metadata.jellyfinArtists') }}
            </p>
            <p class="mt-1 text-2xl font-semibold text-primary">
              {{ jellyfinCounts.jellyfin }}
            </p>
          </div>
          <div class="surface rounded-2xl p-4">
            <p class="text-xs uppercase text-base-content/40">
              {{ t('metadata.localArtistFolders') }}
            </p>
            <p class="mt-1 text-2xl font-semibold">
              {{ jellyfinCounts.folders }}
            </p>
          </div>
        </div>

        <div
          v-if="jellyfinMessage"
          class="surface mb-5 flex items-center gap-3 rounded-2xl p-4 text-sm"
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
          <span>{{ jellyfinMessage }}</span>
        </div>

        <div
          v-if="artistReconciliation"
          class="mb-5 flex flex-wrap items-center justify-between gap-3"
        >
          <h3 class="text-sm font-semibold text-base-content/80">
            {{ t('metadata.artistReconciliation') }}
          </h3>
          <p class="text-xs text-base-content/45">
            {{ t('metadata.lastChecked') }} {{ lastReconciled }}
          </p>
        </div>

        <div v-if="artistReconciliation" class="grid gap-3 lg:grid-cols-4">
          <div
            v-for="bucket in reconciliationBuckets"
            :key="bucket.key"
            class="surface rounded-2xl p-4"
          >
            <div class="flex items-start justify-between gap-3">
              <div>
                <p class="text-xs uppercase text-base-content/40">
                  {{ bucket.label }}
                </p>
                <p class="mt-1 text-2xl font-semibold text-primary">
                  {{ bucket.count }}
                </p>
              </div>
              <Icon :icon="bucket.icon" class="h-5 w-5 text-primary/70" />
            </div>
            <ul
              v-if="bucket.items.length > 0"
              class="mt-3 max-h-36 space-y-1 overflow-y-auto pr-1 text-xs text-base-content/60"
            >
              <li
                v-for="item in bucket.items.slice(0, 12)"
                :key="`${bucket.key}-${item.name}`"
                class="truncate rounded-lg bg-white/5 px-2 py-1"
              >
                {{ item.name }}
              </li>
            </ul>
            <p v-else class="mt-3 text-xs text-base-content/40">
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
const applyingArtistImages = ref({})
const fixedArtistImages = ref({})
const repairingAllImages = ref(false)
const artistImageSummary = ref({ scanned: 0, matched: 0, total: 0 })
const artistReconciliation = ref(null)
const reconcilingArtists = ref(false)
const refreshingJellyfin = ref(false)
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
  return [
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
})

const jellyfinCounts = computed(() => {
  const counts = artistReconciliation.value?.counts || {}
  return {
    jellyfin: counts.jellyfin || 0,
    folders: counts.folders || 0,
    tags: counts.tags || 0,
  }
})

const jellyfinLibraryName = computed(() => {
  const library = artistReconciliation.value?.library || {}
  return library.name || library.id || t('metadata.notCheckedYet')
})

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

function pendingArtistImageItems(items) {
  return (items || []).filter((item) => !fixedArtistImages.value[itemKey(item)])
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
  completedArtistImages.value =
    data.completed || completedArtistImages.value
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

async function reconcileArtists() {
  reconcilingArtists.value = true
  jellyfinMessage.value = ''
  jellyfinError.value = false
  try {
    const res = await API.reconcileJellyfinArtists()
    artistReconciliation.value = res.data
    lastReconciled.value = new Date().toLocaleString()
    jellyfinMessage.value = t('metadata.jellyfinReconcileOk')
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
      items.value = items.value.filter((existing) => existing.file !== item.file)
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

async function repairAllArtistImages() {
  repairingAllImages.value = true
  for (const item of [...artistImageItems.value]) {
    // eslint-disable-next-line no-await-in-loop
    await applyArtistImage(item)
  }
  repairingAllImages.value = false
}
</script>
