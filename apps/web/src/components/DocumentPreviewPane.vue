<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'

import { listChunks, originalFileUrl, previewDocument, type DocumentChunk, type DocumentPreview } from '@/api/documents'
import MarkdownContent from '@/components/MarkdownContent.vue'

const props = withDefaults(defineProps<{
  documentId: string
  filename: string
  chunkId?: string
}>(), {
  chunkId: '',
})

const preview = ref<DocumentPreview | null>(null)
const chunks = ref<DocumentChunk[]>([])
const loading = ref(false)
const root = ref<HTMLElement | null>(null)

const extension = computed(() => props.filename.split('.').pop()?.toLowerCase() ?? '')
const isPdf = computed(() => extension.value === 'pdf')
const isMarkdown = computed(() => extension.value === 'md')
const targetChunk = computed(() => chunks.value.find((item) => item.id === props.chunkId))
const pdfSource = computed(() => {
  const page = targetChunk.value?.page_number
  return `${originalFileUrl(props.documentId)}${page ? `#page=${page}&view=FitH` : '#view=FitH'}`
})
const formatLabel = computed(() => ({
  pdf: 'PDF 原文件',
  md: 'Markdown 原文',
  docx: 'Word 原文',
  txt: 'TXT 原文',
}[extension.value] ?? '原文件'))

function normalize(value: string): string {
  return value.replace(/\s+/g, ' ').trim()
}

function segmentHighlighted(content: string): boolean {
  const target = targetChunk.value
  if (!target) return false
  const segmentText = normalize(content)
  const targetText = normalize(target.content)
  if (!segmentText || !targetText) return false
  return targetText.includes(segmentText) || segmentText.includes(targetText.slice(0, 80))
}

function showSection(index: number): boolean {
  const segments = preview.value?.segments ?? []
  const current = segments[index]?.section_title
  return Boolean(current && current !== segments[index - 1]?.section_title)
}

async function focusCitation(): Promise<void> {
  await nextTick()
  root.value?.querySelector('.document-paragraph.highlighted')?.scrollIntoView({
    behavior: 'smooth',
    block: 'center',
  })
}

async function loadPreview(): Promise<void> {
  if (!props.documentId) return
  loading.value = true
  try {
    const [previewResult, chunkResult] = await Promise.all([
      previewDocument(props.documentId),
      listChunks(props.documentId),
    ])
    preview.value = previewResult
    chunks.value = chunkResult
    await focusCitation()
  } finally {
    loading.value = false
  }
}

watch(() => [props.documentId, props.chunkId], () => void loadPreview(), { immediate: true })
</script>

<template>
  <div ref="root" class="direct-document-preview" v-loading="loading">
    <div class="direct-preview-toolbar">
      <span><i></i>{{ formatLabel }} · 当前窗口直接预览</span>
      <el-tag v-if="targetChunk" type="warning" effect="light">
        已定位引用{{ targetChunk.page_number ? ` · 第 ${targetChunk.page_number} 页` : '' }}
      </el-tag>
    </div>

    <template v-if="isPdf">
      <aside v-if="targetChunk" class="citation-location-banner">
        <strong>引用原文</strong>
        <p>{{ targetChunk.content }}</p>
      </aside>
      <iframe
        :key="pdfSource"
        class="pdf-direct-preview"
        :src="pdfSource"
        :title="`${filename} 原文件预览`"
      ></iframe>
    </template>

    <div v-else-if="preview?.segments.length" class="document-page-preview">
      <article
        v-for="(segment, index) in preview.segments"
        :key="segment.index"
        class="document-paragraph"
        :class="{ highlighted: segmentHighlighted(segment.content) }"
      >
        <h3 v-if="showSection(index)">{{ segment.section_title }}</h3>
        <MarkdownContent v-if="isMarkdown" :content="segment.content" />
        <p v-else>{{ segment.content }}</p>
        <span v-if="segmentHighlighted(segment.content)" class="citation-highlight-label">引用位置</span>
      </article>
    </div>
    <el-empty v-else-if="!loading" description="原文件暂无可预览内容" />
  </div>
</template>
