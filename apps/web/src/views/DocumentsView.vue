<script setup lang="ts">
import { ElMessage, ElMessageBox, type UploadRequestOptions } from 'element-plus'
import { nextTick, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import {
  deleteDocument,
  listChunks,
  listDocuments,
  reindexDocument,
  uploadDocument,
  type DocumentChunk,
  type DocumentItem,
} from '@/api/documents'

const route = useRoute()
const router = useRouter()
const documents = ref<DocumentItem[]>([])
const chunks = ref<DocumentChunk[]>([])
const loading = ref(false)
const detailVisible = ref(false)
const currentDocument = ref<DocumentItem | null>(null)

function statusType(status: string): 'success' | 'warning' | 'danger' | 'info' {
  if (status === 'indexed') return 'success'
  if (status === 'failed') return 'danger'
  return status === 'indexing' ? 'warning' : 'info'
}
function statusLabel(status: string): string {
  return status
}
function formatBytes(bytes: number): string {
  return bytes < 1024 * 1024
    ? `${(bytes / 1024).toFixed(1)} KB`
    : `${(bytes / 1024 / 1024).toFixed(1)} MB`
}
async function refresh(): Promise<void> {
  loading.value = true
  try {
    documents.value = await listDocuments()
  } finally {
    loading.value = false
  }
}
async function handleUpload(options: UploadRequestOptions): Promise<void> {
  try {
    const result = await uploadDocument(options.file)
    ElMessage.success(
      result.action === 'unchanged' ? '内容未变化，无需重复索引' : '文件已保存并完成索引流程',
    )
    await refresh()
  } catch (error: unknown) {
    ElMessage.error(error instanceof Error ? error.message : '上传失败')
  }
}
async function handleDelete(item: DocumentItem): Promise<void> {
  await ElMessageBox.confirm(`确认删除「${item.filename}」？删除后不再参与问答。`, '删除文档', {
    type: 'warning',
  })
  await deleteDocument(item.id)
  ElMessage.success('已删除')
  await refresh()
}
async function handleReindex(item: DocumentItem): Promise<void> {
  await reindexDocument(item.id)
  ElMessage.success('重建索引流程已完成')
  await refresh()
}
async function openDetail(item: DocumentItem): Promise<void> {
  currentDocument.value = item
  chunks.value = await listChunks(item.id)
  detailVisible.value = true
  await router.replace({ path: `/documents/${item.id}`, query: route.query })
  await nextTick()
  const chunk = typeof route.query.chunk === 'string' ? route.query.chunk : ''
  document
    .getElementById(`chunk-${chunk}`)
    ?.scrollIntoView({ behavior: 'smooth', block: 'center' })
}
watch(detailVisible, (visible) => {
  if (!visible && route.params.id) void router.replace('/documents')
})
onMounted(async () => {
  await refresh()
  const id = typeof route.params.id === 'string' ? route.params.id : ''
  const item = documents.value.find((document) => document.id === id)
  if (item) await openDetail(item)
})
</script>

<template>
  <el-card shadow="never">
    <div class="toolbar">
      <div>
        <strong>知识库文件</strong>
        <p>支持 Markdown、TXT、PDF、Word；同名同内容跳过，同名新内容替换。</p>
      </div>
      <el-upload
        :show-file-list="false"
        accept=".md,.txt,.pdf,.docx"
        :http-request="handleUpload"
      ><el-button type="primary">上传文档</el-button></el-upload>
    </div>
    <el-table :data="documents" v-loading="loading" empty-text="暂无文档，请先上传测试资料">
      <el-table-column prop="filename" label="文件名" min-width="220" />
      <el-table-column label="状态" width="120">
        <template #default="scope">
          <el-tooltip :content="scope.row.error_message ?? ''" :disabled="!scope.row.error_message">
            <el-tag :type="statusType(scope.row.status)">{{ statusLabel(scope.row.status) }}</el-tag>
          </el-tooltip>
        </template>
      </el-table-column>
      <el-table-column label="版本" width="80"><template #default="scope">v{{ scope.row.version }}</template></el-table-column>
      <el-table-column label="分块" prop="chunk_count" width="80" />
      <el-table-column label="大小" width="110"><template #default="scope">{{ formatBytes(scope.row.size_bytes) }}</template></el-table-column>
      <el-table-column label="更新时间" width="180"><template #default="scope">{{ new Date(scope.row.updated_at).toLocaleString() }}</template></el-table-column>
      <el-table-column label="操作" width="230" fixed="right">
        <template #default="scope">
          <el-button link type="primary" @click="openDetail(scope.row)">查看原文</el-button>
          <el-button link @click="handleReindex(scope.row)">重建</el-button>
          <el-button link type="danger" @click="handleDelete(scope.row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
  <el-drawer v-model="detailVisible" :title="currentDocument?.filename" size="55%">
    <el-empty v-if="!chunks.length" description="暂无可定位文本；请检查索引状态" />
    <article
      v-for="chunk in chunks"
      :id="`chunk-${chunk.id}`"
      :key="chunk.id"
      class="source-chunk"
      :class="{ highlighted: route.query.chunk === chunk.id }"
    >
      <header>
        <span>#{{ chunk.chunk_index + 1 }} {{ chunk.section_title ?? '原文片段' }}</span>
        <small>{{ chunk.page_number ? `第 ${chunk.page_number} 页` : '' }} {{ chunk.paragraph_start ? `第 ${chunk.paragraph_start} 段` : '' }}</small>
      </header>
      <p>{{ chunk.content }}</p>
    </article>
  </el-drawer>
</template>
