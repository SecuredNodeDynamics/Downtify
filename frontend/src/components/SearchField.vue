<template>
  <div class="relative min-w-0" :class="rootClass">
    <input
      :id="inputId"
      ref="inputRef"
      :value="modelValue"
      type="text"
      :inputmode="inputmode"
      :enterkeyhint="enterkeyhint"
      :autocomplete="autocomplete"
      :autocapitalize="autocapitalize"
      :autocorrect="autocorrect"
      :spellcheck="spellcheck"
      :placeholder="placeholder"
      :aria-label="ariaLabel || placeholder"
      :disabled="disabled"
      class="input-modern w-full"
      :class="[sizeClasses.input, sizeClasses.inputPad]"
      @input="onInput"
      @keyup.enter="onEnter"
      @focus="onFocus"
      @blur="onBlur"
    />
    <button
      type="button"
      class="absolute right-1.5 top-1/2 inline-flex -translate-y-1/2 items-center justify-center rounded-full shadow-glow-sm transition hover:scale-105 active:scale-95 disabled:opacity-60"
      :class="[
        sizeClasses.action,
        showClear
          ? 'border-2 border-error bg-base-100/85 text-error hover:bg-base-100'
          : 'bg-primary text-primary-content',
      ]"
      :disabled="disabled || (!hasText && submitDisabled)"
      :aria-label="
        showClear ? t('library.clearSearch') : submitAriaLabel || undefined
      "
      @pointerdown="onActionPointerDown"
      @click="onAction"
    >
      <span
        v-if="submitLoading"
        class="loading loading-spinner"
        :class="sizeClasses.spinner"
      />
      <Icon v-else-if="showClear" icon="clarity:times-line" class="h-4 w-4" />
      <Icon
        v-else-if="submitIcon === 'download'"
        icon="clarity:download-line"
        class="h-4 w-4"
      />
      <Icon v-else icon="clarity:search-line" class="h-4 w-4" />
    </button>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useI18n } from '/src/i18n'
import {
  FIELD_VISIBILITY_RETRY_DELAYS_MS,
  isFieldHiddenByKeyboard,
  shouldTrackFieldVisibility,
} from '/src/model/searchFieldVisibility'

const props = defineProps({
  modelValue: {
    type: String,
    default: '',
  },
  placeholder: {
    type: String,
    default: '',
  },
  ariaLabel: {
    type: String,
    default: '',
  },
  inputId: {
    type: String,
    default: '',
  },
  size: {
    type: String,
    default: 'standard',
    validator: (value) => ['large', 'standard', 'compact'].includes(value),
  },
  rootClass: {
    type: String,
    default: '',
  },
  inputmode: {
    type: String,
    default: 'text',
  },
  enterkeyhint: {
    type: String,
    default: 'search',
  },
  autocomplete: {
    type: String,
    default: 'off',
  },
  autocapitalize: {
    type: String,
    default: 'off',
  },
  autocorrect: {
    type: String,
    default: 'off',
  },
  spellcheck: {
    type: [Boolean, String],
    default: false,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  submitDisabled: {
    type: Boolean,
    default: false,
  },
  submitLoading: {
    type: Boolean,
    default: false,
  },
  submitIcon: {
    type: String,
    default: 'search',
    validator: (value) => ['search', 'download'].includes(value),
  },
  submitAriaLabel: {
    type: String,
    default: '',
  },
  // When true, keep the field scrolled above the on-screen keyboard on focus.
  // Used by the full-screen Home hero, whose centered layout would otherwise
  // leave the field hidden behind the keyboard on mobile/APK.
  keepVisibleOnFocus: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue', 'submit', 'clear'])

const { t } = useI18n()
const inputRef = ref(null)
const retryTimers = []
let viewportResizeCleanup = null

const hasText = computed(() => Boolean(String(props.modelValue || '').trim()))
const showClear = computed(() => hasText.value && !props.submitLoading)

const sizeClasses = computed(() => {
  if (props.size === 'large') {
    return {
      input: 'h-14 text-base',
      inputPad: 'pr-14',
      action: 'h-11 w-11',
      spinner: 'loading-sm',
    }
  }
  if (props.size === 'compact') {
    return {
      input: 'h-11 text-sm',
      inputPad: 'pr-14',
      action: 'h-9 w-9',
      spinner: 'loading-xs',
    }
  }
  return {
    input: 'h-12 text-sm',
    inputPad: 'pr-14',
    action: 'h-9 w-9',
    spinner: 'loading-xs',
  }
})

function onInput(event) {
  emit('update:modelValue', event.target.value)
}

function dismissKeyboard() {
  const input = inputRef.value
  if (input) {
    input.blur()
  }
  const active = document.activeElement
  if (active instanceof HTMLElement && active !== document.body) {
    active.blur()
  }
}

function clear() {
  emit('update:modelValue', '')
  emit('clear')
  dismissKeyboard()
}

function onActionPointerDown(event) {
  if (!showClear.value || props.submitLoading) return
  event.preventDefault()
}

function onAction() {
  if (props.submitLoading) return
  if (hasText.value) {
    clear()
    return
  }
  emit('submit')
}

function onEnter() {
  if (hasText.value && props.submitDisabled) return
  if (hasText.value) {
    emit('submit')
    return
  }
  emit('submit')
}

function ensureFieldVisible() {
  const input = inputRef.value
  if (!input || !input.isConnected) return

  const viewport = typeof window !== 'undefined' ? window.visualViewport : null
  let hidden = true
  if (viewport) {
    const rect = input.getBoundingClientRect()
    hidden = isFieldHiddenByKeyboard({
      fieldTop: rect.top,
      fieldBottom: rect.bottom,
      viewportOffsetTop: viewport.offsetTop,
      viewportHeight: viewport.height,
      margin: 16,
    })
  }
  if (!hidden) return

  try {
    input.scrollIntoView({ block: 'center' })
  } catch {
    input.scrollIntoView()
  }
}

function clearVisibilityWatchers() {
  while (retryTimers.length) {
    window.clearTimeout(retryTimers.pop())
  }
  if (viewportResizeCleanup) {
    viewportResizeCleanup()
    viewportResizeCleanup = null
  }
}

function onFocus() {
  if (typeof window === 'undefined') return
  if (
    !shouldTrackFieldVisibility({
      enabled: props.keepVisibleOnFocus,
      viewportWidth: window.innerWidth,
    })
  ) {
    return
  }

  clearVisibilityWatchers()

  // The keyboard and (on Android) the viewport resize asynchronously, so react
  // to the visualViewport resize when available and fall back to timed passes.
  const viewport = window.visualViewport
  if (viewport) {
    const onResize = () => ensureFieldVisible()
    viewport.addEventListener('resize', onResize)
    viewportResizeCleanup = () =>
      viewport.removeEventListener('resize', onResize)
  }
  for (const delay of FIELD_VISIBILITY_RETRY_DELAYS_MS) {
    retryTimers.push(window.setTimeout(ensureFieldVisible, delay))
  }
}

function onBlur() {
  clearVisibilityWatchers()
}

onBeforeUnmount(clearVisibilityWatchers)

function focus(options) {
  inputRef.value?.focus(options)
}

defineExpose({ focus, inputRef })
</script>
