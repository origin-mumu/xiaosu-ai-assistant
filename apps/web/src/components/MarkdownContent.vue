<script setup lang="ts">
import DOMPurify from 'dompurify'
import { marked } from 'marked'
import { computed } from 'vue'

const props = defineProps<{ content: string }>()

const html = computed(() => {
  const parsed = marked.parse(props.content, {
    async: false,
    breaks: true,
    gfm: true,
  }) as string
  const sanitized = DOMPurify.sanitize(parsed)
  const template = document.createElement('template')
  template.innerHTML = sanitized
  template.content.querySelectorAll('table').forEach((table) => {
    const wrapper = document.createElement('div')
    wrapper.className = 'markdown-table-scroll'
    wrapper.setAttribute('role', 'region')
    wrapper.setAttribute('aria-label', '表格（可横向滚动）')
    table.parentNode?.insertBefore(wrapper, table)
    wrapper.appendChild(table)
  })
  return template.innerHTML
})
</script>

<template>
  <div class="markdown-content" v-html="html"></div>
</template>
