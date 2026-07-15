<template>
  <div class="queue-page">
    <div class="queue-chrome">
      <ServerConnectionPrompt class="mb-3" />

      <div class="queue-toolbar">
        <div class="queue-tabs">
          <button
            type="button"
            class="queue-tab-btn"
            :class="
              activeTab === 'queue'
                ? 'queue-tab-btn-active'
                : 'queue-tab-btn-inactive'
            "
            @click="activeTab = 'queue'"
          >
            {{ t('queue.tab') }}
            <span
              v-if="pt.activeDownloadCount.value > 0"
              class="queue-tab-count"
            >
              {{ pt.activeDownloadCount.value }}
            </span>
          </button>
          <button
            type="button"
            class="queue-tab-btn"
            :class="
              activeTab === 'history'
                ? 'queue-tab-btn-active'
                : 'queue-tab-btn-inactive'
            "
            @click="activeTab = 'history'"
          >
            {{ t('history.tab') }}
          </button>
          <button
            type="button"
            class="queue-tab-btn"
            :class="
              activeTab === 'failed'
                ? 'queue-tab-btn-active'
                : 'queue-tab-btn-inactive'
            "
            @click="activeTab = 'failed'"
          >
            {{ t('history.failed') }}
            <span v-if="failedHistory.length > 0" class="queue-tab-count">
              {{ failedHistory.length }}
            </span>
          </button>
          <button
            type="button"
            class="queue-tab-btn"
            :class="
              activeTab === 'manage'
                ? 'queue-tab-btn-active'
                : 'queue-tab-btn-inactive'
            "
            @click="activeTab = 'manage'"
          >
            {{ t('manage.tab') }}
            <span v-if="manageItems.length > 0" class="queue-tab-count">
              {{ manageItems.length }}
            </span>
          </button>
        </div>

        <button
          v-if="activeTab === 'queue' && pt.activeDownloadCount.value > 0"
          type="button"
          class="queue-action-btn text-error/70 hover:text-error"
          @click="onClearAll"
          :title="t('queue.clearAll')"
        >
          <Icon icon="clarity:trash-line" class="h-4 w-4" />
          <span class="hidden sm:inline">{{ t('queue.clearAll') }}</span>
        </button>

        <button
          v-if="activeTab === 'history' && sortedHistory.length > 0"
          type="button"
          class="queue-action-btn text-error/70 hover:text-error"
          @click="onClearHistory"
          :title="t('history.clear')"
        >
          <Icon icon="clarity:trash-line" class="h-4 w-4" />
          <span class="hidden sm:inline">{{ t('history.clear') }}</span>
        </button>
      </div>

      <div
        v-if="activeTab === 'failed' && failedHistory.length > 0"
        class="failed-tab-actions"
      >
        <button
          type="button"
          class="failed-bulk-btn failed-bulk-retry-btn"
          :disabled="retryAllLoading"
          @click="retryAllFailedHistory"
        >
          <span
            v-if="retryAllLoading"
            class="loading loading-spinner loading-xs"
          />
          <Icon v-else icon="clarity:refresh-line" class="h-4 w-4" />
          <span>{{ t('failed.retryAll') }}</span>
        </button>
        <button
          type="button"
          class="failed-bulk-btn failed-bulk-delete-btn"
          :disabled="deleteAllLoading"
          @click="deleteAllFailedHistory"
        >
          <span
            v-if="deleteAllLoading"
            class="loading loading-spinner loading-xs"
          />
          <Icon v-else icon="clarity:trash-line" class="h-4 w-4" />
          <span>{{ t('failed.deleteAll') }}</span>
        </button>
      </div>
    </div>

    <div class="queue-body-slot">
      <div
        class="queue-body-shell panel-glow-shell panel-glow-shell-grow surface min-h-0 rounded-3xl"
      >
        <div class="queue-panel panel-glow-inner p-3 sm:p-5">
          <div class="queue-scroll-body">
            <template v-if="activeTab === 'manage'">
              <div
                v-if="manageError"
                class="mb-3 flex items-center gap-3 rounded-2xl border border-error/20 bg-error/10 p-3 text-sm text-error"
              >
                <Icon
                  icon="clarity:exclamation-circle-line"
                  class="h-5 w-5 shrink-0"
                />
                <span>{{ manageError }}</span>
              </div>

              <div
                v-if="manageLoading && manageItems.length === 0"
                class="space-y-2"
              >
                <div
                  v-for="n in 5"
                  :key="n"
                  class="skeleton h-16 rounded-2xl"
                />
              </div>

              <div v-else-if="manageItems.length === 0" class="queue-empty">
                <Icon
                  icon="clarity:library-line"
                  class="mb-4 h-12 w-12 text-base-content/20"
                />
                <p class="text-sm text-base-content/50">
                  {{ t('manage.empty') }}
                </p>
                <p class="mt-1 text-xs text-base-content/40">
                  {{ t('manage.emptyHint') }}
                </p>
              </div>

              <template v-else>
                <div class="manage-controls">
                  <label class="manage-search">
                    <Icon
                      icon="clarity:search-line"
                      class="h-4 w-4 shrink-0 text-base-content/40"
                    />
                    <input
                      v-model="manageQuery"
                      type="text"
                      class="manage-search-input"
                      :placeholder="t('manage.search')"
                    />
                    <button
                      v-if="manageQuery"
                      type="button"
                      class="icon-btn"
                      @click="manageQuery = ''"
                    >
                      <Icon icon="clarity:times-line" class="h-4 w-4" />
                    </button>
                  </label>
                  <span class="manage-count">{{ manageCountLabel }}</span>
                </div>

                <div class="manage-view-tabs">
                  <button
                    type="button"
                    class="manage-view-btn"
                    :class="
                      manageView === 'artists'
                        ? 'manage-view-btn-active'
                        : 'manage-view-btn-inactive'
                    "
                    @click="manageView = 'artists'"
                  >
                    {{ t('manage.artists') }}
                  </button>
                  <button
                    type="button"
                    class="manage-view-btn"
                    :class="
                      manageView === 'albums'
                        ? 'manage-view-btn-active'
                        : 'manage-view-btn-inactive'
                    "
                    @click="manageView = 'albums'"
                  >
                    {{ t('manage.albums') }}
                  </button>
                  <button
                    type="button"
                    class="manage-view-btn"
                    :class="
                      manageView === 'tracks'
                        ? 'manage-view-btn-active'
                        : 'manage-view-btn-inactive'
                    "
                    @click="manageView = 'tracks'"
                  >
                    {{ t('manage.tracks') }}
                  </button>
                </div>

                <div
                  v-if="filteredManageItems.length === 0"
                  class="queue-empty"
                >
                  <Icon
                    icon="clarity:search-line"
                    class="mb-4 h-10 w-10 text-base-content/20"
                  />
                  <p class="text-sm text-base-content/50">
                    {{ t('manage.noMatches') }}
                  </p>
                </div>

                <ul v-else-if="manageView === 'artists'" class="queue-list">
                  <li
                    v-for="artist in manageArtists"
                    :key="artist.name"
                    class="queue-item"
                  >
                    <div class="queue-item-cover">
                      <CoverImage
                        :src="coverSourcesForArtist(artist).src"
                        :fallbacks="coverSourcesForArtist(artist).fallbacks"
                        :alt="artist.name"
                        img-class="h-full w-full object-cover"
                      >
                        <template #fallback>
                          <Icon
                            icon="clarity:user-line"
                            class="h-5 w-5 text-base-content/35"
                          />
                        </template>
                      </CoverImage>
                    </div>

                    <div class="min-w-0 flex-1">
                      <p class="truncate text-sm font-semibold">
                        {{ artist.name }}
                      </p>
                      <p class="truncate text-xs text-base-content/60">
                        {{
                          t('manage.artistMeta', {
                            tracks: artist.files.length,
                            albums: artist.albumCount,
                          })
                        }}
                      </p>
                    </div>

                    <div class="flex shrink-0 items-center gap-1">
                      <button
                        type="button"
                        class="icon-btn icon-btn-danger"
                        :disabled="
                          manageDeleting[`artist:${artist.name}`] === true
                        "
                        @click="onManageDeleteArtist(artist)"
                        :title="t('manage.deleteArtist')"
                      >
                        <span
                          v-if="
                            manageDeleting[`artist:${artist.name}`] === true
                          "
                          class="loading loading-spinner loading-xs"
                        />
                        <Icon
                          v-else
                          icon="clarity:trash-line"
                          class="h-4 w-4"
                        />
                      </button>
                    </div>
                  </li>
                </ul>

                <ul v-else-if="manageView === 'albums'" class="queue-list">
                  <li
                    v-for="album in manageAlbums"
                    :key="album.key"
                    class="queue-item"
                  >
                    <div class="queue-item-cover">
                      <CoverImage
                        :src="coverSourcesFor(album.coverFile).src"
                        :fallbacks="coverSourcesFor(album.coverFile).fallbacks"
                        :alt="album.name"
                        img-class="h-full w-full object-cover"
                      >
                        <template #fallback>
                          <Icon
                            icon="clarity:album-line"
                            class="h-5 w-5 text-base-content/35"
                          />
                        </template>
                      </CoverImage>
                    </div>

                    <div class="min-w-0 flex-1">
                      <p class="truncate text-sm font-semibold">
                        {{ album.name }}
                      </p>
                      <p class="truncate text-xs text-base-content/60">
                        {{ album.artist }}
                      </p>
                      <p class="truncate text-xs text-base-content/40">
                        {{
                          t('manage.albumMeta', { count: album.files.length })
                        }}
                      </p>
                    </div>

                    <div class="flex shrink-0 items-center gap-1">
                      <button
                        type="button"
                        class="icon-btn icon-btn-danger"
                        :disabled="
                          manageDeleting[`album:${album.key}`] === true
                        "
                        @click="onManageDeleteAlbum(album)"
                        :title="t('manage.deleteAlbum')"
                      >
                        <span
                          v-if="manageDeleting[`album:${album.key}`] === true"
                          class="loading loading-spinner loading-xs"
                        />
                        <Icon
                          v-else
                          icon="clarity:trash-line"
                          class="h-4 w-4"
                        />
                      </button>
                    </div>
                  </li>
                </ul>

                <ul v-else class="queue-list">
                  <li
                    v-for="item in filteredManageItems"
                    :key="item.file"
                    class="queue-item"
                  >
                    <div class="queue-item-cover">
                      <CoverImage
                        :src="coverSourcesFor(item.file).src"
                        :fallbacks="coverSourcesFor(item.file).fallbacks"
                        :alt="item.title"
                        img-class="h-full w-full object-cover"
                      >
                        <template #fallback>
                          <Icon
                            icon="clarity:music-note-line"
                            class="h-5 w-5 text-base-content/35"
                          />
                        </template>
                      </CoverImage>
                    </div>

                    <div class="min-w-0 flex-1">
                      <p class="truncate text-sm font-semibold">
                        {{ item.title || t('common.unknownTrack') }}
                      </p>
                      <p class="truncate text-xs text-base-content/60">
                        {{ item.artistsLabel }}
                      </p>
                      <p
                        v-if="item.album"
                        class="truncate text-xs text-base-content/40"
                      >
                        {{ item.album }}
                      </p>
                    </div>

                    <div class="flex shrink-0 items-center gap-1">
                      <button
                        type="button"
                        class="icon-btn icon-btn-danger"
                        :disabled="manageDeleting[item.file] === true"
                        @click="onManageDelete(item)"
                        :title="t('manage.delete')"
                      >
                        <span
                          v-if="manageDeleting[item.file] === true"
                          class="loading loading-spinner loading-xs"
                        />
                        <Icon
                          v-else
                          icon="clarity:trash-line"
                          class="h-4 w-4"
                        />
                      </button>
                    </div>
                  </li>
                </ul>
              </template>
            </template>

            <template v-else-if="activeTab === 'queue'">
              <div
                v-if="pt.activeDownloadCount.value === 0"
                class="queue-empty"
              >
                <Icon
                  icon="clarity:download-line"
                  class="mb-4 h-12 w-12 text-base-content/20"
                />
                <p class="text-sm text-base-content/50">
                  {{ t('queue.empty') }}
                </p>
                <p class="mt-1 text-xs text-base-content/40">
                  {{ t('queue.emptyHint') }}
                </p>
              </div>

              <ul v-else class="queue-list">
                <li
                  v-for="item in visibleActiveQueue"
                  :key="item.song.song_id || item.song.name"
                  class="queue-item"
                >
                  <div class="queue-item-cover">
                    <CoverImage
                      v-if="item.song.cover_url"
                      :src="coverSrc(item.song.cover_url)"
                      :alt="item.song.name"
                      img-class="h-full w-full object-cover"
                    >
                      <template #fallback>
                        <Icon
                          icon="clarity:music-note-line"
                          class="h-5 w-5 text-base-content/35"
                        />
                      </template>
                    </CoverImage>
                    <Icon
                      v-else
                      icon="clarity:music-note-line"
                      class="h-5 w-5 text-base-content/35"
                    />
                  </div>

                  <div class="min-w-0 flex-1">
                    <div class="mb-0.5 flex items-center gap-2">
                      <span class="truncate text-sm font-semibold">
                        {{ item.song.name }}
                      </span>
                      <span :class="statusClass(item)" class="shrink-0">
                        {{ item.message || item.web_status }}
                      </span>
                    </div>
                    <p class="truncate text-xs text-base-content/60">
                      {{ artistsOf(item.song) }}
                    </p>
                    <p
                      v-if="item.song.album_name"
                      class="truncate text-xs text-base-content/40"
                    >
                      {{ item.song.album_name }}
                    </p>
                  </div>

                  <div class="flex shrink-0 items-center gap-1">
                    <div
                      v-if="item.progress > 0 && !item.isErrored()"
                      class="radial-progress text-primary"
                      :style="`--value:${item.progress}; --size:2.5rem; --thickness:3px`"
                    >
                      <span class="text-[10px] font-semibold">
                        {{ Math.round(item.progress) }}%
                      </span>
                    </div>
                    <span
                      v-else-if="!item.isErrored()"
                      class="loading loading-spinner loading-sm text-primary"
                    />

                    <button
                      type="button"
                      class="icon-btn icon-btn-danger"
                      @click="dm.remove(item.song)"
                      :title="t('queue.removeFromQueue')"
                    >
                      <Icon icon="clarity:trash-line" class="h-4 w-4" />
                    </button>
                  </div>
                </li>
              </ul>
              <p v-if="hiddenActiveQueueCount > 0" class="queue-overflow-note">
                {{ hiddenActiveQueueCount }} more queued items hidden while the
                app catches up.
              </p>
            </template>

            <template v-else-if="activeTab === 'failed'">
              <div
                v-if="historyError"
                class="mb-3 flex items-center gap-3 rounded-2xl border border-error/20 bg-error/10 p-3 text-sm text-error"
              >
                <Icon
                  icon="clarity:exclamation-circle-line"
                  class="h-5 w-5 shrink-0"
                />
                <span>{{ historyError }}</span>
              </div>

              <div
                v-if="historyLoading && failedHistory.length === 0"
                class="grid gap-3 sm:grid-cols-2"
              >
                <div
                  v-for="n in 4"
                  :key="n"
                  class="skeleton h-40 rounded-2xl"
                />
              </div>

              <div v-else-if="failedHistory.length === 0" class="queue-empty">
                <Icon
                  icon="clarity:success-standard-line"
                  class="mb-4 h-10 w-10 text-base-content/20"
                />
                <p class="text-sm text-base-content/50">
                  {{ t('failed.empty') }}
                </p>
                <p class="mt-1 text-xs text-base-content/40">
                  {{ t('failed.emptyHint') }}
                </p>
              </div>

              <template v-else>
                <ul class="failed-grid">
                  <li
                    v-for="item in failedHistory"
                    :key="item.id"
                    class="failed-card"
                  >
                  <div class="flex min-w-0 gap-3">
                    <div class="queue-item-cover h-14 w-14">
                      <CoverImage
                        v-if="item.song?.cover_url"
                        :src="coverSrc(item.song.cover_url)"
                        :alt="item.title"
                        img-class="h-full w-full object-cover"
                      >
                        <template #fallback>
                          <Icon
                            icon="clarity:music-note-line"
                            class="h-5 w-5 text-base-content/35"
                          />
                        </template>
                      </CoverImage>
                      <Icon
                        v-else
                        icon="clarity:music-note-line"
                        class="h-5 w-5 text-base-content/35"
                      />
                    </div>

                    <div class="min-w-0 flex-1">
                      <div class="mb-1 flex items-start justify-between gap-2">
                        <p
                          class="failed-card-title text-sm font-semibold leading-snug"
                        >
                          {{ failedItemTitle(item) }}
                        </p>
                        <span class="badge-error-soft shrink-0">
                          {{ t('history.failed') }}
                        </span>
                      </div>
                      <p class="truncate text-xs text-base-content/60">
                        {{ failedItemArtists(item) }}
                      </p>
                      <p class="mt-1 text-xs text-base-content/40">
                        {{ formatDate(historyDate(item)) }}
                      </p>
                    </div>
                  </div>

                  <p
                    v-if="item.error"
                    class="failed-card-error mt-3 rounded-xl border border-error/15 bg-error/5 px-3 py-2 text-xs leading-relaxed text-error/80"
                  >
                    {{ item.error }}
                  </p>

                  <div class="mt-3 grid grid-cols-2 gap-2">
                    <button
                      type="button"
                      class="failed-action-btn text-primary hover:border-primary/40 hover:bg-primary/10"
                      :disabled="retrying[item.id] === true"
                      @click="retryHistory(item)"
                    >
                      <span
                        v-if="retrying[item.id] === true"
                        class="loading loading-spinner loading-xs"
                      />
                      <Icon
                        v-else
                        icon="clarity:refresh-line"
                        class="h-4 w-4"
                      />
                      <span>{{ t('history.retry') }}</span>
                    </button>
                    <button
                      type="button"
                      class="failed-action-btn text-error/75 hover:border-error/40 hover:bg-error/10 hover:text-error"
                      :disabled="deletingHistory[item.id] === true"
                      @click="deleteFailedHistory(item)"
                    >
                      <span
                        v-if="deletingHistory[item.id] === true"
                        class="loading loading-spinner loading-xs"
                      />
                      <Icon v-else icon="clarity:trash-line" class="h-4 w-4" />
                      <span>{{ t('failed.delete') }}</span>
                    </button>
                  </div>
                  </li>
                </ul>
              </template>
            </template>

            <template v-else>
              <div
                v-if="historyError"
                class="mb-3 flex items-center gap-3 rounded-2xl border border-error/20 bg-error/10 p-3 text-sm text-error"
              >
                <Icon
                  icon="clarity:exclamation-circle-line"
                  class="h-5 w-5 shrink-0"
                />
                <span>{{ historyError }}</span>
              </div>

              <div
                v-if="historyLoading && sortedHistory.length === 0"
                class="space-y-2"
              >
                <div
                  v-for="n in 4"
                  :key="n"
                  class="skeleton h-16 rounded-2xl"
                />
              </div>

              <div v-else-if="sortedHistory.length === 0" class="queue-empty">
                <Icon
                  icon="clarity:history-line"
                  class="mb-4 h-10 w-10 text-base-content/20"
                />
                <p class="text-sm text-base-content/50">
                  {{ t('history.empty') }}
                </p>
                <p class="mt-1 text-xs text-base-content/40">
                  {{ t('history.emptyHint') }}
                </p>
              </div>

              <ul v-else class="queue-list">
                <li
                  v-for="item in sortedHistory"
                  :key="item.id"
                  class="queue-item"
                  :class="{
                    'queue-item-playable': canOpenHistoryInPlayer(item),
                  }"
                >
                  <button
                    v-if="canOpenHistoryInPlayer(item)"
                    type="button"
                    class="queue-item-main"
                    :title="t('history.openInPlayer')"
                    @click="openHistoryInPlayer(item)"
                  >
                    <div class="queue-item-cover">
                      <CoverImage
                        v-if="item.song?.cover_url"
                        :src="coverSrc(item.song.cover_url)"
                        :alt="item.title"
                        img-class="h-full w-full object-cover"
                      >
                        <template #fallback>
                          <Icon
                            icon="clarity:music-note-line"
                            class="h-5 w-5 text-base-content/35"
                          />
                        </template>
                      </CoverImage>
                      <Icon
                        v-else
                        icon="clarity:music-note-line"
                        class="h-5 w-5 text-base-content/35"
                      />
                    </div>

                    <div class="min-w-0 flex-1 text-left">
                      <div class="mb-0.5 flex items-center gap-2">
                        <span class="truncate text-sm font-semibold">
                          {{ item.title || t('common.unknownTrack') }}
                        </span>
                        <span
                          :class="historyStatusClass(item)"
                          class="shrink-0"
                        >
                          {{ historyStatusLabel(item) }}
                        </span>
                      </div>
                      <p class="truncate text-xs text-base-content/60">
                        {{ item.artists || t('common.unknownArtist') }}
                      </p>
                      <p class="truncate text-xs text-base-content/40">
                        {{ formatDate(historyDate(item)) }}
                      </p>
                    </div>
                  </button>

                  <template v-else>
                    <div class="queue-item-cover">
                      <CoverImage
                        v-if="item.song?.cover_url"
                        :src="coverSrc(item.song.cover_url)"
                        :alt="item.title"
                        img-class="h-full w-full object-cover"
                      >
                        <template #fallback>
                          <Icon
                            icon="clarity:music-note-line"
                            class="h-5 w-5 text-base-content/35"
                          />
                        </template>
                      </CoverImage>
                      <Icon
                        v-else
                        icon="clarity:music-note-line"
                        class="h-5 w-5 text-base-content/35"
                      />
                    </div>

                    <div class="min-w-0 flex-1">
                      <div class="mb-0.5 flex items-center gap-2">
                        <span class="truncate text-sm font-semibold">
                          {{ item.title || t('common.unknownTrack') }}
                        </span>
                        <span
                          :class="historyStatusClass(item)"
                          class="shrink-0"
                        >
                          {{ historyStatusLabel(item) }}
                        </span>
                      </div>
                      <p class="truncate text-xs text-base-content/60">
                        {{ item.artists || t('common.unknownArtist') }}
                      </p>
                      <p class="truncate text-xs text-base-content/40">
                        {{ formatDate(historyDate(item)) }}
                        <span v-if="item.error">- {{ item.error }}</span>
                      </p>
                    </div>
                  </template>

                  <div class="flex shrink-0 items-center gap-1">
                    <a
                      v-if="item.filename"
                      class="icon-btn"
                      :href="API.downloadFileURL(item.filename)"
                      download
                      :title="t('history.downloadFile')"
                    >
                      <Icon icon="clarity:download-line" class="h-4 w-4" />
                    </a>
                    <button
                      v-if="item.status === 'error'"
                      type="button"
                      class="icon-btn text-primary hover:bg-primary/10"
                      :disabled="retrying[item.id] === true"
                      @click="retryHistory(item)"
                      :title="t('history.retry')"
                    >
                      <span
                        v-if="retrying[item.id] === true"
                        class="loading loading-spinner loading-xs"
                      />
                      <Icon
                        v-else
                        icon="clarity:refresh-line"
                        class="h-4 w-4"
                      />
                    </button>
                  </div>
                </li>
              </ul>
            </template>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import {
  ref,
  computed,
  onMounted,
  onActivated,
  onDeactivated,
  onUnmounted,
  watch,
} from 'vue'
import { useRouter } from 'vue-router'
import { Icon } from '@iconify/vue'
import API from '../model/api'
import CoverImage from './CoverImage.vue'
import ServerConnectionPrompt from './ServerConnectionPrompt.vue'
import {
  useProgressTracker,
  useDownloadManager,
  scanDeviceLibraryPath,
} from '../model/download'
import { useDownloadHistory } from '../model/downloadHistory'
import {
  canOpenHistoryInPlayer,
  setPlayerNavigation,
} from '../model/playerNavigation'
import {
  normalizeLibraryItem,
  libraryArtistsLabel,
  matchesLibraryTrackItem,
  groupAlbums,
  groupArtists,
} from '../model/library'
import {
  getCachedLibraryItems,
  onLibraryChanged,
} from '../model/librarySession'
import { useDownloadRefresh } from '../model/downloadRefresh'
import { useI18n } from '../i18n'

const router = useRouter()
const downloadRefresh = useDownloadRefresh()

const pt = useProgressTracker()
const dm = useDownloadManager()
const {
  sortedHistory,
  failedHistory,
  historyRevision,
  refreshDownloadHistory,
  clearDownloadHistoryState,
  removeHistoryItem,
  markHistoryRetrying,
  historyDate,
} = useDownloadHistory()
const { t } = useI18n()
const activeTab = ref('queue')
const historyLoading = ref(false)
const historyError = ref('')
const retrying = ref({})
const retryAllLoading = ref(false)
const deleteAllLoading = ref(false)
const deletingHistory = ref({})
let historyFetchSeq = 0

const manageItems = ref([])
const manageLoading = ref(false)
const manageError = ref('')
const manageQuery = ref('')
const manageView = ref('tracks')
const manageDeleting = ref({})
let manageFetchSeq = 0
let stopManageLibraryListener = null
const MAX_VISIBLE_QUEUE_ITEMS = 20

const visibleActiveQueue = computed(() =>
  pt.activeQueue.value.slice(0, MAX_VISIBLE_QUEUE_ITEMS)
)
const hiddenActiveQueueCount = computed(() =>
  Math.max(0, pt.activeQueue.value.length - MAX_VISIBLE_QUEUE_ITEMS)
)

const filteredManageItems = computed(() => {
  const query = manageQuery.value.trim()
  if (!query) return manageItems.value
  return manageItems.value.filter((item) =>
    matchesLibraryTrackItem(item, query)
  )
})

const manageGroupOptions = computed(() => ({
  unknownArtist: t('common.unknownArtist'),
}))

const manageAlbums = computed(() =>
  groupAlbums(filteredManageItems.value, manageGroupOptions.value)
)

const manageArtists = computed(() =>
  groupArtists(filteredManageItems.value, manageGroupOptions.value)
)

const manageResultCount = computed(() => {
  if (manageView.value === 'albums') return manageAlbums.value.length
  if (manageView.value === 'artists') return manageArtists.value.length
  return filteredManageItems.value.length
})

const manageCountLabel = computed(() => {
  const count = manageResultCount.value
  if (manageView.value === 'albums') {
    return count === 1
      ? t('manage.albumCount', { count })
      : t('manage.albumCountPlural', { count })
  }
  if (manageView.value === 'artists') {
    return count === 1
      ? t('manage.artistCount', { count })
      : t('manage.artistCountPlural', { count })
  }
  return count === 1
    ? t('manage.count', { count })
    : t('manage.countPlural', { count })
})

const retryableFailedHistory = computed(() => failedHistory.value)

function coverSrc(url) {
  return API.mediaUrl(url)
}

function coverSourcesFor(file) {
  return API.coverSourcesForFile(file)
}

function coverSourcesForArtist(artist) {
  return API.coverSourcesForArtist(artist.name, artist.previewFiles)
}

function decorateLibraryItems(items) {
  const unknownArtist = t('common.unknownArtist')
  return (items || [])
    .map((raw) => {
      const normalized = normalizeLibraryItem(raw, { unknownArtist })
      return {
        ...normalized,
        artistsLabel:
          libraryArtistsLabel(normalized, { unknownArtist }) || unknownArtist,
      }
    })
    .sort(
      (a, b) =>
        a.artistsLabel.localeCompare(b.artistsLabel) ||
        a.album.localeCompare(b.album) ||
        a.title.localeCompare(b.title)
    )
}

async function refreshManage({ background = false } = {}) {
  const seq = ++manageFetchSeq
  if (!background) manageLoading.value = true
  manageError.value = ''
  try {
    const res = await API.getLibraryFiles()
    if (seq !== manageFetchSeq) return
    manageItems.value = decorateLibraryItems(res.data || [])
  } catch {
    if (seq !== manageFetchSeq) return
    manageError.value = t('manage.failedLoad')
  } finally {
    if (seq === manageFetchSeq && !background) {
      manageLoading.value = false
    }
  }
}

function loadManageFromCache() {
  const cached = getCachedLibraryItems()
  if (cached?.length) {
    manageItems.value = decorateLibraryItems(cached)
  }
}

async function onManageDelete(item) {
  if (!confirm(t('manage.deletePrompt', { title: item.title }))) return
  manageDeleting.value = { ...manageDeleting.value, [item.file]: true }
  try {
    await API.deleteDownload(item.file)
    scanDeviceLibraryPath(item.file)
    manageItems.value = manageItems.value.filter((m) => m.file !== item.file)
  } catch {
    manageError.value = t('manage.failedDelete')
  } finally {
    manageDeleting.value = { ...manageDeleting.value, [item.file]: false }
  }
}

async function deleteManageFiles(key, files) {
  const targets = (files || []).filter(Boolean)
  if (targets.length === 0) return
  manageDeleting.value = { ...manageDeleting.value, [key]: true }
  const removed = new Set()
  try {
    for (const file of targets) {
      await API.deleteDownload(file)
      scanDeviceLibraryPath(file)
      removed.add(file)
    }
  } catch {
    manageError.value = t('manage.failedDelete')
  } finally {
    if (removed.size > 0) {
      manageItems.value = manageItems.value.filter((m) => !removed.has(m.file))
    }
    manageDeleting.value = { ...manageDeleting.value, [key]: false }
  }
}

function onManageDeleteAlbum(album) {
  if (
    !confirm(
      t('manage.deleteAlbumPrompt', {
        name: album.name,
        count: album.files.length,
      })
    )
  ) {
    return
  }
  return deleteManageFiles(`album:${album.key}`, album.files)
}

function onManageDeleteArtist(artist) {
  if (
    !confirm(
      t('manage.deleteArtistPrompt', {
        name: artist.name,
        count: artist.files.length,
      })
    )
  ) {
    return
  }
  return deleteManageFiles(`artist:${artist.name}`, artist.files)
}

async function onClearAll() {
  if (!confirm(t('queue.clearAllPrompt'))) return
  await dm.clearAll()
}

function artistsOf(song) {
  if (Array.isArray(song.artists) && song.artists.length) {
    return song.artists.join(', ')
  }
  return song.artist || t('common.unknownArtist')
}

function statusClass(item) {
  if (item.isErrored()) return 'badge-error-soft'
  if (item.isDownloading()) return 'badge-neutral-soft'
  return 'badge-neutral-soft'
}

function historyStatusClass(item) {
  if (item.status === 'error') return 'badge-error-soft'
  if (item.status === 'done') return 'badge-soft'
  return 'badge-neutral-soft'
}

function historyStatusLabel(item) {
  if (item.status === 'error') return t('history.failed')
  if (item.status === 'done') return t('history.done')
  if (item.status === 'skipped') return t('history.skipped')
  if (item.status === 'downloading') return t('history.downloading')
  return t('history.queued')
}

async function refreshHistory() {
  const seq = ++historyFetchSeq
  historyLoading.value = true
  historyError.value = ''
  try {
    const ok = await refreshDownloadHistory()
    if (seq !== historyFetchSeq) return
    if (!ok) historyError.value = t('history.failedLoad')
  } finally {
    if (seq === historyFetchSeq) {
      historyLoading.value = false
    }
  }
}

async function retryHistory(item) {
  retrying.value = { ...retrying.value, [item.id]: true }
  try {
    await API.retryHistoryItem(item.id)
    markHistoryRetrying(item.id)
  } catch {
    historyError.value = t('history.failedRetry')
  } finally {
    retrying.value = { ...retrying.value, [item.id]: false }
  }
}

async function retryAllFailedHistory() {
  const items = retryableFailedHistory.value.filter(
    (item) => item?.id !== undefined && retrying.value[item.id] !== true
  )
  if (!items.length || retryAllLoading.value) return

  retryAllLoading.value = true
  historyError.value = ''
  retrying.value = {
    ...retrying.value,
    ...Object.fromEntries(items.map((item) => [item.id, true])),
  }

  try {
    await Promise.all(items.map((item) => API.retryHistoryItem(item.id)))
    for (const item of items) {
      markHistoryRetrying(item.id)
    }
  } catch {
    historyError.value = t('failed.failedRetryAll')
  } finally {
    const nextRetrying = { ...retrying.value }
    for (const item of items) {
      nextRetrying[item.id] = false
    }
    retrying.value = nextRetrying
    retryAllLoading.value = false
  }
}

async function deleteFailedHistory(item) {
  const historyId = Number(item?.id)
  if (!Number.isInteger(historyId)) {
    historyError.value = t('failed.failedDelete')
    return
  }
  historyError.value = ''
  deletingHistory.value = { ...deletingHistory.value, [historyId]: true }
  try {
    await API.deleteHistoryItem(historyId)
    removeHistoryItem(historyId)
  } catch {
    historyError.value = t('failed.failedDelete')
  } finally {
    deletingHistory.value = { ...deletingHistory.value, [historyId]: false }
  }
}

async function deleteAllFailedHistory() {
  const items = failedHistory.value.filter((item) => item?.id !== undefined)
  if (!items.length || deleteAllLoading.value) return
  if (!confirm(t('failed.deleteAllPrompt', { count: items.length }))) return

  deleteAllLoading.value = true
  historyError.value = ''
  deletingHistory.value = {
    ...deletingHistory.value,
    ...Object.fromEntries(items.map((item) => [item.id, true])),
  }

  try {
    await Promise.all(items.map((item) => API.deleteHistoryItem(item.id)))
    for (const item of items) {
      removeHistoryItem(item.id)
    }
  } catch {
    historyError.value = t('failed.failedDeleteAll')
  } finally {
    const nextDeleting = { ...deletingHistory.value }
    for (const item of items) {
      nextDeleting[item.id] = false
    }
    deletingHistory.value = nextDeleting
    deleteAllLoading.value = false
  }
}

function failedItemTitle(item) {
  return (
    item?.title ||
    item?.song?.name ||
    item?.song?.title ||
    t('common.unknownTrack')
  )
}

function failedItemArtists(item) {
  const artists = item?.artists || item?.song?.artists || item?.song?.artist
  if (Array.isArray(artists)) return artists.filter(Boolean).join(', ')
  return artists || t('common.unknownArtist')
}

async function onClearHistory() {
  if (!confirm(t('history.clearPrompt'))) return
  await API.clearHistory()
  clearDownloadHistoryState()
}

function formatDate(value) {
  if (!value) return ''
  try {
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: 'medium',
      timeStyle: 'short',
    }).format(new Date(value))
  } catch {
    return value
  }
}

function openHistoryInPlayer(item) {
  if (!canOpenHistoryInPlayer(item)) return
  setPlayerNavigation({
    file: item.filename,
    artist: item.artists || '',
    album: item.album || '',
  })
  router.push({ name: 'Player' })
}

// Refresh whatever the active tab shows; the live Queue tab streams over the
// WebSocket so it has nothing to pull. Returning the promise lets the header
// refresh store await the fetch (and keep its spinner up) before settling.
function refreshActiveTab() {
  if (activeTab.value === 'history' || activeTab.value === 'failed') {
    return refreshHistory()
  }
  if (activeTab.value === 'manage') return refreshManage()
  return Promise.resolve()
}

function syncMobileFailedAction() {
  if (typeof window === 'undefined') return
  if (
    activeTab.value !== 'failed' ||
    retryableFailedHistory.value.length === 0
  ) {
    clearMobileFailedAction()
    return
  }
  window.dispatchEvent(
    new CustomEvent('downtify:mobile-route-action', {
      detail: {
        routeName: 'Download',
        icon: retryAllLoading.value
          ? 'clarity:refresh-line'
          : 'clarity:refresh-line',
        label: t('failed.retryAll'),
        title: t('failed.retryAll'),
        onClick: () => {
          void retryAllFailedHistory()
        },
      },
    })
  )
}

function clearMobileFailedAction() {
  if (typeof window === 'undefined') return
  window.dispatchEvent(
    new CustomEvent('downtify:clear-mobile-route-action', {
      detail: { routeName: 'Download' },
    })
  )
}

function syncDownloadRefreshVisibility() {
  downloadRefresh.setVisible(
    activeTab.value === 'history' ||
      activeTab.value === 'failed' ||
      activeTab.value === 'manage'
  )
}

watch(activeTab, (tab) => {
  if (tab === 'history' || tab === 'failed') void refreshHistory()
  if (tab === 'manage') {
    loadManageFromCache()
    void refreshManage({ background: manageItems.value.length > 0 })
  }
  syncDownloadRefreshVisibility()
  syncMobileFailedAction()
})

watch(
  () => historyRevision.value,
  () => {
    void refreshHistory()
  }
)

watch(
  [retryableFailedHistory, retryAllLoading],
  () => {
    syncMobileFailedAction()
  },
  { deep: true }
)

function registerManageLibraryListener() {
  if (stopManageLibraryListener) return
  stopManageLibraryListener = onLibraryChanged(() => {
    if (activeTab.value === 'manage') {
      void refreshManage({ background: true })
    }
  })
}

onMounted(() => {
  void refreshHistory()
  loadManageFromCache()
  registerManageLibraryListener()
  downloadRefresh.register(refreshActiveTab)
  syncDownloadRefreshVisibility()
  syncMobileFailedAction()
})

onActivated(() => {
  void refreshHistory()
  registerManageLibraryListener()
  downloadRefresh.register(refreshActiveTab)
  syncDownloadRefreshVisibility()
  syncMobileFailedAction()
  if (activeTab.value === 'manage') {
    void refreshManage({ background: manageItems.value.length > 0 })
  }
})

onDeactivated(() => {
  if (stopManageLibraryListener) {
    stopManageLibraryListener()
    stopManageLibraryListener = null
  }
  downloadRefresh.unregister()
  clearMobileFailedAction()
})

onUnmounted(() => {
  downloadRefresh.unregister()
  clearMobileFailedAction()
})
</script>

<style scoped>
.queue-page {
  @apply mx-auto flex w-full max-w-4xl flex-1 flex-col gap-2 min-h-0 overflow-hidden px-4 py-3 sm:px-6 lg:py-8;
}

.queue-chrome {
  @apply shrink-0 space-y-3;
  background: transparent;
}

.queue-toolbar {
  @apply flex flex-wrap items-center gap-2;
  background: transparent;
  box-shadow: none;
}

.queue-tabs {
  @apply inline-flex min-w-full flex-1 gap-0.5 overflow-hidden rounded-full border border-white/10 bg-base-100/75 p-1 sm:min-w-0 sm:gap-1;
}

.queue-tab-btn {
  @apply flex min-w-0 flex-1 items-center justify-center gap-1 whitespace-nowrap rounded-full px-1 py-2 text-center font-medium transition-colors sm:gap-1.5 sm:px-4 sm:text-sm;
  font-size: clamp(0.625rem, 2.75vw, 0.875rem);
}

.queue-tab-btn-active {
  @apply bg-primary text-primary-content shadow-glow-sm;
}

.queue-tab-btn-inactive {
  @apply text-base-content/65 hover:bg-white/5 hover:text-base-content;
}

.queue-tab-count {
  @apply inline-flex h-4 min-w-[1rem] shrink items-center justify-center rounded-full bg-primary-content/15 px-1 text-[9px] font-semibold sm:h-5 sm:min-w-[1.25rem] sm:px-1.5 sm:text-[11px];
}

.queue-action-btn {
  @apply inline-flex h-10 shrink-0 items-center gap-1.5 rounded-full border border-white/10 bg-base-100/85 px-3 text-sm font-medium transition-colors hover:bg-base-100;
}

.queue-body-slot {
  @apply flex min-h-0 flex-1 flex-col overflow-hidden;
}

.queue-body-shell {
  @apply overflow-hidden;
}

.queue-panel {
  @apply flex min-h-0 flex-1 flex-col overflow-hidden;
}

.queue-scroll-body {
  @apply min-h-0 flex-1 overflow-x-hidden overflow-y-auto;
  -webkit-overflow-scrolling: touch;
  overscroll-behavior-y: contain;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.queue-scroll-body::-webkit-scrollbar {
  display: none;
  width: 0;
  height: 0;
}

.queue-empty {
  @apply flex flex-col items-center px-4 py-12 text-center sm:py-16;
}

.manage-controls {
  @apply mb-3 flex items-center gap-3;
}

.manage-search {
  @apply flex min-w-0 flex-1 items-center gap-2 rounded-full border border-white/10 bg-base-100/75 px-3 py-2;
}

.manage-search-input {
  @apply min-w-0 flex-1 bg-transparent text-sm outline-none placeholder:text-base-content/40;
}

.manage-count {
  @apply shrink-0 text-xs text-base-content/50;
}

.manage-view-tabs {
  @apply mb-3 inline-flex gap-1 rounded-full border border-white/10 bg-base-100/75 p-1;
}

.manage-view-btn {
  @apply rounded-full px-3 py-1.5 text-xs font-medium transition-colors sm:px-4 sm:text-sm;
}

.manage-view-btn-active {
  @apply bg-primary text-primary-content shadow-glow-sm;
}

.manage-view-btn-inactive {
  @apply text-base-content/65 hover:bg-white/5 hover:text-base-content;
}

.queue-list {
  @apply space-y-2;
}

.queue-overflow-note {
  @apply mt-3 rounded-xl border border-white/10 bg-base-100/45 px-3 py-2 text-center text-xs font-medium text-base-content/50;
}

.failed-tab-actions {
  @apply flex flex-wrap justify-end gap-2;
}

.failed-bulk-btn {
  @apply inline-flex h-10 flex-1 items-center justify-center gap-2 rounded-xl border px-4 text-sm font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-60 sm:flex-none;
}

.failed-bulk-retry-btn {
  @apply border-primary/30 bg-primary/10 text-primary hover:border-primary/50 hover:bg-primary/15;
}

.failed-bulk-delete-btn {
  @apply border-error/30 bg-error/10 text-error hover:border-error/50 hover:bg-error/15;
}

.failed-grid {
  @apply grid gap-3 sm:grid-cols-2;
}

.failed-card {
  @apply min-w-0 overflow-hidden rounded-2xl border border-error/15 bg-error/[0.04] p-3 shadow-lg shadow-black/10;
}

.failed-card-title,
.failed-card-error {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.failed-action-btn {
  @apply flex h-11 items-center justify-center gap-2 rounded-xl border border-white/10 bg-base-100/60 px-3 text-sm font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-50;
}

.queue-item {
  @apply flex items-center gap-3 rounded-2xl border border-white/10 bg-white/5 p-3 transition-colors sm:gap-4 sm:p-3.5;
}

.queue-item-playable {
  @apply hover:border-primary/25 hover:bg-white/[0.07] active:bg-white/10;
}

.queue-item-main {
  @apply flex min-w-0 flex-1 items-center gap-3 text-left sm:gap-4;
}

.queue-item-cover {
  @apply relative flex h-11 w-11 shrink-0 items-center justify-center overflow-hidden rounded-xl bg-primary/10 text-primary sm:h-12 sm:w-12;
}

@media (min-width: 1024px) {
  .queue-page {
    @apply gap-4 py-8;
  }
}
</style>
