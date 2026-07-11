<template>
  <input id="mobile-search-sheet" type="checkbox" class="modal-toggle" />
  <div
    class="modal modal-top mobile-search-modal lg:hidden"
    @click.self="close"
  >
    <div class="modal-box mobile-search-sheet">
      <form class="flex items-center" @submit.prevent="submit">
        <SearchField
          ref="searchFieldRef"
          root-class="w-full flex-1"
          input-id="mobile-search-input"
          v-model="query"
          :placeholder="placeholder"
          :submit-icon="'search'"
          :submit-disabled="!canSubmit"
          @submit="submit"
          @clear="onClear"
        />
      </form>
      <p v-if="isPlayerSearch" class="mt-2 text-xs text-base-content/50">
        {{ t('search.libraryHint') }}
      </p>
    </div>
    <label
      for="mobile-search-sheet"
      class="modal-backdrop"
      aria-hidden="true"
      @click.prevent="close"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

import router from '../router'
import { useMobileSearch } from '../model/mobileSearch'
import { useSearchManager } from '../model/search'
import { buildSearchRoute } from '../model/searchNavigation'
import { useI18n } from '../i18n'
import SearchField from './SearchField.vue'

const route = useRoute()
const { t } = useI18n()
const sm = useSearchManager()
const mobileSearch = useMobileSearch()

const searchFieldRef = ref(null)
const query = ref('')

const isPlayerSearch = computed(() => route.name === 'Player')

const placeholder = computed(() =>
  isPlayerSearch.value
    ? t('search.libraryPlaceholder')
    : t('search.placeholder')
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

function onClear() {
  if (isPlayerSearch.value) {
    mobileSearch.clearLibraryFilter()
  }
}

function submit() {
  const value = query.value.trim()
  if (!value) return

  if (isPlayerSearch.value) {
    mobileSearch.setLibraryFilter(value)
    close()
    return
  }

  if (!sm.isValidSearch(value) && !sm.isValidURL(value)) return

  close()
  router.push(buildSearchRoute(value))
}

function syncQueryFromContext() {
  if (isPlayerSearch.value) {
    query.value = mobileSearch.libraryFilter.value
    return
  }
  query.value = sm.searchTerm.value || ''
}

function focusInput() {
  const field = searchFieldRef.value
  if (!field) return
  try {
    const el = document.getElementById('mobile-search-input')
    if (el) {
      el.readOnly = true
      field.focus({ preventScroll: true })
      el.readOnly = false
      field.focus({ preventScroll: true })
      if (typeof el.setSelectionRange === 'function') {
        const end = el.value.length
        el.setSelectionRange(end, end)
      }
      return
    }
    field.focus({ preventScroll: true })
  } catch {
    field.focus({ preventScroll: true })
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
