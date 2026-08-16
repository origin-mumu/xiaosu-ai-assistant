<script setup lang="ts">
import { ChatDotRound, CircleCheck, Document, Warning } from '@element-plus/icons-vue'
import { computed, onMounted, ref } from 'vue'

import { listMessages, type QuestionAnswerLog } from '@/api/admin'
import { listDocuments, type DocumentItem } from '@/api/documents'
import { fetchDependencyHealth, type DependencyHealth } from '@/api/health'

const documents = ref<DocumentItem[]>([])
const exchanges = ref<QuestionAnswerLog[]>([])
const health = ref<DependencyHealth | null>(null)
const loading = ref(true)
const errorMessage = ref('')
const todayCount = computed(() => {
  const today = new Date().toDateString()
  return exchanges.value.filter(
    (item) => new Date(item.question.created_at).toDateString() === today,
  ).length
})
const failedCount = computed(() => exchanges.value.filter(
  (item) => (item.answer?.status ?? 'unanswered') !== 'completed',
).length)

onMounted(async () => {
  try {
    const [documentItems, messagePage, dependencyHealth] = await Promise.all([
      listDocuments(),
      listMessages({ pageSize: 500 }),
      fetchDependencyHealth(),
    ])
    documents.value = documentItems
    exchanges.value = messagePage.items
    health.value = dependencyHealth
  } catch (error: unknown) {
    errorMessage.value = error instanceof Error ? error.message : '加载失败'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <el-alert v-if="errorMessage" :title="errorMessage" type="error" show-icon :closable="false" />
  <section class="metric-grid" v-loading="loading">
    <article class="metric-card metric-card-blue">
      <div class="metric-card-top"><span class="metric-icon"><el-icon><Document /></el-icon></span><span class="metric-badge">KNOWLEDGE</span></div>
      <div class="metric">{{ documents.length }}</div>
      <div class="metric-title">知识库文档</div>
      <p class="metric-note"><span class="mini-dot"></span>{{ documents.filter((item) => item.status === 'indexed').length }} 份已完成索引</p>
    </article>
    <article class="metric-card metric-card-violet">
      <div class="metric-card-top"><span class="metric-icon"><el-icon><ChatDotRound /></el-icon></span><span class="metric-badge">TODAY</span></div>
      <div class="metric">{{ todayCount }}</div>
      <div class="metric-title">今日提问</div>
      <p class="metric-note"><span class="mini-dot"></span>Web 与钉钉统一统计</p>
    </article>
    <article class="metric-card metric-card-orange">
      <div class="metric-card-top"><span class="metric-icon"><el-icon><Warning /></el-icon></span><span class="metric-badge">ALERT</span></div>
      <div class="metric">{{ failedCount }}</div>
      <div class="metric-title">未答与失败</div>
      <p class="metric-note"><span class="mini-dot"></span>区分知识缺失与系统错误</p>
    </article>
    <article class="metric-card metric-card-green">
      <div class="metric-card-top"><span class="metric-icon"><el-icon><CircleCheck /></el-icon></span><span class="metric-badge">HEALTHY</span></div>
      <div class="metric metric-status">{{ health?.status === 'ok' ? '在线' : '离线' }}</div>
      <div class="metric-title">系统状态</div>
      <p class="metric-note"><span class="mini-dot"></span>数据库 {{ health?.database ?? '检查中' }}</p>
    </article>
  </section>

  <el-card shadow="never" class="section-card integration-card">
    <template #header>
      <div class="card-heading">
        <div><strong>接入检查</strong><p>模型、向量服务与凭证的实时配置状态</p></div>
        <span class="health-pill"><i></i>运行正常</span>
      </div>
    </template>
    <div class="integration-grid">
      <div class="integration-item"><span>对话模型</span><strong>{{ health?.llm_model ?? '-' }}</strong><small>LLM</small></div>
      <div class="integration-item"><span>向量模型</span><strong>{{ health?.embedding_model ?? '-' }}</strong><small>EMBEDDING</small></div>
      <div class="integration-item"><span>向量维度</span><strong>{{ health?.embedding_dimension ?? '-' }}</strong><small>DIMENSION</small></div>
      <div class="integration-item"><span>API Key</span><strong>{{ health?.model_api_key_configured ? '已配置' : '待填写' }}</strong><small>{{ health?.model_api_key_configured ? 'READY' : 'ACTION NEEDED' }}</small></div>
    </div>
  </el-card>
</template>
