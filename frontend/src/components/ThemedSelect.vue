<template>
  <div ref="rootRef" class="themed-select relative min-w-0 w-full">
    <button
      ref="triggerRef"
      type="button"
      class="select-modern h-10 w-full text-left"
      :class="{ 'opacity-50': disabled }"
      :disabled="disabled"
      :aria-expanded="open"
      aria-haspopup="listbox"
      @click="toggle"
    >
      <span
        class="block truncate"
        :class="{ 'text-base-content/40': !displayLabel }"
      >
        {{ displayLabel || placeholder }}
      </span>
    </button>

    <Teleport to="body">
      <div
        v-if="open"
        ref="menuRef"
        class="themed-select-menu fixed z-[200]"
        :style="menuStyle"
        role="listbox"
      >
        <button
          v-for="option in options"
          :key="option.value"
          type="button"
          class="themed-select-option"
          :class="{
            'themed-select-option-active': option.value === modelValue,
          }"
          role="option"
          :aria-selected="option.value === modelValue"
          @click="select(option.value)"
        >
          <span class="truncate">{{ option.label }}</span>
        </button>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: '',
  },
  options: {
    type: Array,
    default: () => [],
  },
  placeholder: {
    type: String,
    default: '',
  },
  disabled: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue'])

const rootRef = ref(null)
const triggerRef = ref(null)
const menuRef = ref(null)
const open = ref(false)
const menuStyle = ref({ top: '0px', left: '0px', width: '0px' })

const displayLabel = computed(() => {
  const value = String(props.modelValue || '')
  if (!value) return ''
  const match = props.options.find((option) => option.value === value)
  return match?.label || value
})

function close() {
  open.value = false
}

function updateMenuPosition() {
  const trigger = triggerRef.value
  if (!trigger) return
  const rect = trigger.getBoundingClientRect()
  menuStyle.value = {
    top: `${rect.bottom + 6}px`,
    left: `${rect.left}px`,
    width: `${rect.width}px`,
  }
}

async function toggle() {
  if (props.disabled) return
  open.value = !open.value
  if (open.value) {
    await nextTick()
    updateMenuPosition()
  }
}

function select(value) {
  emit('update:modelValue', value)
  close()
}

function onDocumentClick(event) {
  if (!open.value) return
  const target = event.target
  if (rootRef.value?.contains(target) || menuRef.value?.contains(target)) {
    return
  }
  close()
}

function onDocumentKeydown(event) {
  if (event.key === 'Escape') {
    close()
  }
}

function onViewportChange() {
  if (open.value) {
    updateMenuPosition()
  }
}

onMounted(() => {
  document.addEventListener('click', onDocumentClick)
  document.addEventListener('keydown', onDocumentKeydown)
  window.addEventListener('resize', onViewportChange)
  window.addEventListener('scroll', onViewportChange, true)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', onDocumentClick)
  document.removeEventListener('keydown', onDocumentKeydown)
  window.removeEventListener('resize', onViewportChange)
  window.removeEventListener('scroll', onViewportChange, true)
})
</script>
