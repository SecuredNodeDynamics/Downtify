<template>
  <input id="mobile-search-sheet" type="checkbox" class="modal-toggle" />
  <div class="modal modal-top lg:hidden">
    <div class="modal-box mobile-search-sheet safe-top">
      <form class="flex items-center gap-2" @submit.prevent="submit">
        <div class="relative min-w-0 flex-1">
          <input
            id="mobile-search-input"
            ref="inputRef"
            v-model="query"
            type="text"
            inputmode="search"
            enterkeyhint="search"
            autocomplete="off"
            autocapitalize="off"
            autocorrect="off"
            spellcheck="false"
            class="input-modern h-12 w-full text-sm"
            :placeholder="placeholder"
          />
          <button
            type="submit"
            class="absolute right-1.5 top-1/2 inline-flex h-9 w-9 -translate-y-1/2 items-center justify-center rounded-full bg-primary text-primary-content shadow-glow-sm"
            :disabled="!canSubmit"
          >
            <Icon
              v-if="showDownloadIcon"
              icon="clarity:download-line"
              class="h-4 w-4"
            />
            <Icon v-else icon="clarity:search-line" class="h-4 w-4" />
          </button>
        </div>
        <button
          type="button"
          class="mobile-app-bar-icon shrink-0"
          :title="t('common.cancel')"
          @click="close"
        >
          <Icon icon="clarity:close-line" class="h-5 w-5" />
        </button>
      </form>
      <p v-if="isPlayerSearch" class="mt-2 text-xs text-base-content/50">
        {{ t('search.libraryHint') }}
      </p>
    </div>
    <label for="mobile-search-sheet" class="modal-backdrop" @click="close" />
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { Icon } from '@iconify/vue'
import { useRoute } from 'vue-router'

import router from '../router'
import { useDownloadManager } from '../model/download'
import { useMobileSearch } from '../model/mobileSearch'
import { useSearchManager } from '../model/search'
import { useI18n } from '../i18n'

const route = useRoute()
const { t } = useI18n()
const sm = useSearchManager()
const dm = useDownloadManager()
const mobileSearch = useMobileSearch()

const inputRef = ref(null)
const query = ref('')

const isPlayerSearch = computed(() => route.name === 'Player')

const placeholder = computed(() =>
  isPlayerSearch.value ? t('search.libraryPlaceholder') : t('search.placeholder')
)

const showDownloadIcon = computed(
  () => !isPlayerSearch.value && sm.isValidURL(query.value)
)

const canSubmit = computed(() => {
  const value = query.value.trim()
  if (!value) return false
  if (isPlayerSearch.value) return true
  return sm.isValidSearch(value) || sm.isValidURL(value)
})

function close() {
  mobileSearch.closeSheet()
}

function submit() {
  const value = query.value.trim()
  if (!value) return

  if (isPlayerSearch.value) {
    mobileSearch.setLibraryFilter(value)
    close()
    return
  }

  if (sm.isValidURL(value)) {
    dm.fromURL(value)
    close()
    router.push({ name: 'Download' })
    return
  }

  if (sm.isValidSearch(value)) {
    close()
    router.push({ name: 'Search', params: { query: value } })
  }
}

function syncQueryFromContext() {
  if (isPlayerSearch.value) {
    query.value = mobileSearch.libraryFilter.value
    return
  }
  query.value = sm.searchTerm.value || ''
}

function focusInput() {
  const el = inputRef.value || document.getElementById('mobile-search-input')
  if (!el) return
  try {
    el.readOnly = true
    el.focus({ preventScroll: true })
    el.readOnly = false
    el.focus({ preventScroll: true })
    if (typeof el.setSelectionRange === 'function') {
      const end = el.value.length
      el.setSelectionRange(end, end)
    }
  } catch {
    el.focus({ preventScroll: true })
  }
}

function onSheetOpen() {
  syncQueryFromContext()
  focusInput()
}

function onSheetToggle(event) {
  if (!event.target.checked) return
  onSheetOpen()
}

onMounted(() => {
  mobileSearch.registerFocusHandler(focusInput)
  const sheet = document.getElementById('mobile-search-sheet')
  sheet?.addEventListener('change', onSheetToggle)
})

onUnmounted(() => {
  mobileSearch.registerFocusHandler(null)
  const sheet = document.getElementById('mobile-search-sheet')
  sheet?.removeEventListener('change', onSheetToggle)
})

watch(
  () => route.name,
  (name) => {
    if (name !== 'Player') {
      mobileSearch.clearLibraryFilter()
    }
  }
)
</script>
