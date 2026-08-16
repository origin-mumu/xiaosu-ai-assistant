<script setup lang="ts">
import { Setting, Upload } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox, type UploadRequestOptions } from 'element-plus'
import { nextTick, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import DocumentPreviewPane from '@/components/DocumentPreviewPane.vue'
import {
  deleteDocument,
  listChunks,
  listDocuments,
  reindexDocument,
  uploadDocument,
  type DocumentChunk,
  type DocumentItem,
} from '@/api/documents'
import {
  fetchSettings,
  updateKnowledgeSettings,
  type KnowledgeSettingsUpdate,
} from '@/api/admin'

const route = useRoute()
const router = useRouter()
const documents = ref<DocumentItem[]>([])
const chunks = ref<DocumentChunk[]>([])
const loading = ref(false)
const uploadingCount = ref(0)
const detailVisible = ref(false)
const currentDocument = ref<DocumentItem | null>(null)
const activeDetailTab = ref<'original' | 'chunks'>('original')
const settingsVisible = ref(false)
const settingsSaving = ref(false)
const knowledgeSettings = ref<KnowledgeSettingsUpdate>({
  chunk_size: 700,
  chunk_overlap: 100,
  retrieval_top_k: 5,
  retrieval_min_score: 0.35,
  max_upload_mb: 20,
  embedding_batch_size: 10,
  duplicate_policy: 'replace',
})

function statusType(status: string): 'success' | 'warning' | 'danger' | 'info' {
  if (status === 'indexed') return 'success'
  if (status === 'failed') return 'danger'
  return status === 'indexing' ? 'warning' : 'info'
}
function formatBytes(bytes: number): string {
  return bytes < 1024 * 1024
    ? `${(bytes / 1024).toFixed(1)} KB`
    : `${(bytes / 1024 / 1024).toFixed(1)} MB`
}
async function focusHighlightedSource(): Promise<void> {
  await nextTick()
  const element = document.querySelector('.source-chunk.highlighted')
  element?.scrollIntoView({ behavior: 'smooth', block: 'center' })
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
  uploadingCount.value += 1
  try {
    const result = await uploadDocument(options.file)
    ElMessage.success(
      result.action === 'unchanged'
        ? `「${options.file.name}」已跳过：内容未变或策略为保留`
        : `「${options.file.name}」已完成解析与向量索引（生成 ${result.chunk_count} 个切片）`,
    )
    await refresh()
  } catch (error: unknown) {
    ElMessage.error(`「${options.file.name}」上传失败：${error instanceof Error ? error.message : '网络异常'}`)
  } finally {
    uploadingCount.value = Math.max(0, uploadingCount.value - 1)
  }
}
async function handleDelete(item: DocumentItem): Promise<void> {
  await ElMessageBox.confirm(`确认删除「${item.filename}」？删除后原文件和切片都会移除。`, '删除文档', {
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
async function openDetail(
  item: DocumentItem,
  tab: 'original' | 'chunks' = 'original',
  preserveCitation = false,
): Promise<void> {
  currentDocument.value = item
  activeDetailTab.value = preserveCitation && route.query.chunk ? 'original' : tab
  detailVisible.value = true
  chunks.value = await listChunks(item.id)
  await router.replace({
    path: `/documents/${item.id}`,
    query: preserveCitation ? route.query : {},
  })
  await focusHighlightedSource()
}
async function openSettings(): Promise<void> {
  const settings = await fetchSettings()
  knowledgeSettings.value = {
    chunk_size: settings.chunk_size,
    chunk_overlap: settings.chunk_overlap,
    retrieval_top_k: settings.retrieval_top_k,
    retrieval_min_score: settings.retrieval_min_score,
    max_upload_mb: settings.max_upload_mb,
    embedding_batch_size: settings.embedding_batch_size,
    duplicate_policy: settings.duplicate_policy,
  }
  settingsVisible.value = true
}
async function saveSettings(): Promise<void> {
  if (knowledgeSettings.value.chunk_overlap >= knowledgeSettings.value.chunk_size) {
    ElMessage.warning('分块重叠长度必须小于分块长度')
    return
  }
  settingsSaving.value = true
  try {
    await updateKnowledgeSettings(knowledgeSettings.value)
    settingsVisible.value = false
    ElMessage.success('知识库参数已应用；分块参数将在下次上传或重建索引时生效')
  } finally {
    settingsSaving.value = false
  }
}

watch(detailVisible, (visible) => {
  if (!visible && route.params.id) void router.replace('/documents')
})
watch(activeDetailTab, () => void focusHighlightedSource())
onMounted(async () => {
  await refresh()
  const id = typeof route.params.id === 'string' ? route.params.id : ''
  const item = documents.value.find((document) => document.id === id)
  if (item) await openDetail(item, 'original', true)
})
</script>

<template>
  <el-card shadow="never">
    <div class="toolbar">
      <div>
        <strong>知识库文档</strong>
        <p>原始文件持久化保存，支持批量上传、自动分块与余弦向量索引。</p>
      </div>
      <div class="document-toolbar-actions">
        <el-button :icon="Setting" @click="openSettings">知识库设置</el-button>
        <el-upload
          :show-file-list="false"
          multiple
          accept=".md,.txt,.pdf,.docx"
          :http-request="handleUpload"
        >
          <el-button type="primary" :icon="Upload" :loading="uploadingCount > 0">
            {{ uploadingCount > 0 ? `正在索引 (${uploadingCount})...` : '批量上传文档' }}
          </el-button>
        </el-upload>
      </div>
    </div>
    <el-table :data="documents" v-loading="loading || uploadingCount > 0" empty-text="暂无文档，请先上传测试资料">
      <el-table-column prop="filename" label="文件名" min-width="220" />
      <el-table-column label="状态" width="120">
        <template #default="scope">
          <el-tooltip :content="scope.row.error_message ?? ''" :disabled="!scope.row.error_message">
            <el-tag :type="statusType(scope.row.status)">{{ scope.row.status }}</el-tag>
          </el-tooltip>
        </template>
      </el-table-column>
      <el-table-column label="版本" width="80"><template #default="scope">v{{ scope.row.version }}</template></el-table-column>
      <el-table-column label="切片" prop="chunk_count" width="80" />
      <el-table-column label="大小" width="110"><template #default="scope">{{ formatBytes(scope.row.size_bytes) }}</template></el-table-column>
      <el-table-column label="更新时间" width="180"><template #default="scope">{{ new Date(scope.row.updated_at).toLocaleString() }}</template></el-table-column>
      <el-table-column label="操作" width="330" fixed="right">
        <template #default="scope">
          <div class="document-actions">
            <el-button text type="primary" @click="openDetail(scope.row, 'original')">预览原文</el-button>
            <el-button text type="primary" @click="openDetail(scope.row, 'chunks')">查看切片</el-button>
            <el-button text @click="handleReindex(scope.row)">重建</el-button>
            <el-button text type="danger" @click="handleDelete(scope.row)">删除</el-button>
          </div>
        </template>
      </el-table-column>
    </el-table>
  </el-card>

  <el-drawer v-model="detailVisible" :title="currentDocument?.filename" size="62%" class="document-preview-drawer">
    <el-tabs v-model="activeDetailTab" class="document-detail-tabs">
      <el-tab-pane label="原文预览" name="original">
        <DocumentPreviewPane
          v-if="currentDocument"
          :document-id="currentDocument.id"
          :filename="currentDocument.filename"
          :chunk-id="typeof route.query.chunk === 'string' ? route.query.chunk : ''"
        />
      </el-tab-pane>
      <el-tab-pane :label="`切片分段（${chunks.length}）`" name="chunks">
        <el-empty v-if="!chunks.length" description="暂无切片；请检查索引状态" />
        <article
          v-for="chunk in chunks"
          :id="`chunk-${chunk.id}`"
          :key="chunk.id"
          class="source-chunk"
          :class="{ highlighted: route.query.chunk === chunk.id }"
        >
          <header>
            <span>#{{ chunk.chunk_index + 1 }} {{ chunk.section_title ?? '切片内容' }}</span>
            <small>{{ chunk.page_number ? `第 ${chunk.page_number} 页` : '' }} {{ chunk.paragraph_start ? `第 ${chunk.paragraph_start} 段` : '' }}</small>
          </header>
          <p>{{ chunk.content }}</p>
        </article>
      </el-tab-pane>
    </el-tabs>
  </el-drawer>

  <el-dialog v-model="settingsVisible" title="知识库设置" width="680px">
    <el-form label-position="top" class="knowledge-settings-form">
      <div class="setting-field-grid">
        <el-form-item label="分块长度">
          <el-input-number v-model="knowledgeSettings.chunk_size" :min="200" :max="4000" :step="50" />
          <small>单个索引切片的最大字符数量</small>
        </el-form-item>
        <el-form-item label="分块重叠">
          <el-input-number v-model="knowledgeSettings.chunk_overlap" :min="0" :max="1000" :step="25" />
          <small>保留相邻切片之间的上下文</small>
        </el-form-item>
        <el-form-item label="检索数量 Top K">
          <el-input-number v-model="knowledgeSettings.retrieval_top_k" :min="1" :max="20" />
          <small>每次问答最多取回的候选切片数量</small>
        </el-form-item>
        <el-form-item label="最低相似度">
          <el-input-number v-model="knowledgeSettings.retrieval_min_score" :min="0" :max="1" :step="0.05" :precision="2" />
          <small>低于此分数的切片不会成为引用源</small>
        </el-form-item>
        <el-form-item label="单文件大小上限">
          <el-input-number v-model="knowledgeSettings.max_upload_mb" :min="1" :max="100" :step="5" />
          <small>允许管理员上传的单个文件最大体积（MB）</small>
        </el-form-item>
        <el-form-item label="Embedding 批次">
          <el-input-number v-model="knowledgeSettings.embedding_batch_size" :min="1" :max="50" />
          <small>每次向量化请求处理的切片数量</small>
        </el-form-item>
        <el-form-item label="同名文件处理">
          <el-select v-model="knowledgeSettings.duplicate_policy">
            <el-option label="替换并创建新版本" value="replace" />
            <el-option label="保留已有文件并跳过" value="skip" />
          </el-select>
          <small>控制上传同名但内容不同的文件时如何处理</small>
        </el-form-item>
        <el-form-item label="支持格式">
          <div class="supported-format-list">
            <el-tag effect="plain">PDF</el-tag><el-tag effect="plain">Markdown</el-tag>
            <el-tag effect="plain">Word</el-tag><el-tag effect="plain">TXT</el-tag>
          </div>
          <small>上传后保留原文件，并生成可定位的索引切片</small>
        </el-form-item>
      </div>
    </el-form>
    <template #footer>
      <el-button @click="settingsVisible = false">取消</el-button>
      <el-button type="primary" :loading="settingsSaving" @click="saveSettings">保存配置</el-button>
    </template>
  </el-dialog>
</template>
