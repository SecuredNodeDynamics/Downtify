<template>
  <div class="relative">
    <input
      :id="inputId"
      :value="modelValue"
      :type="revealed ? 'text' : 'password'"
      :autocomplete="autocomplete"
      :inputmode="inputmode"
      :placeholder="placeholder"
      :maxlength="maxlength"
      :aria-label="ariaLabel || placeholder"
      class="input input-bordered w-full rounded-xl pr-12"
      @input="$emit('update:modelValue', $event.target.value)"
    />
    <button
      type="button"
      class="absolute right-1.5 top-1/2 inline-flex h-9 w-9 -translate-y-1/2 items-center justify-center rounded-full text-base-content/55 transition hover:bg-base-content/10 hover:text-base-content"
      :aria-label="
        revealed
          ? t('auth.hideSecret', { name: secretName })
          : t('auth.showSecret', { name: secretName })
      "
      :aria-pressed="revealed"
      @click="revealed = !revealed"
    >
      <Icon
        :icon="revealed ? 'clarity:eye-solid' : 'clarity:eye-line'"
        class="h-5 w-5"
      />
    </button>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useI18n } from '/src/i18n'

const props = defineProps({
  modelValue: { type: String, default: '' },
  placeholder: { type: String, default: '' },
  ariaLabel: { type: String, default: '' },
  label: { type: String, default: '' },
  autocomplete: { type: String, default: 'new-password' },
  inputmode: { type: String, default: 'text' },
  maxlength: { type: [Number, String], default: undefined },
  inputId: { type: String, default: undefined },
})

defineEmits(['update:modelValue'])

const { t } = useI18n()
const revealed = ref(false)

const secretName = computed(
  () => props.label || props.ariaLabel || props.placeholder || t('auth.password')
)
</script>
