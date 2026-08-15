<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { listMessages, type MessageLog } from '@/api/admin'
import { listDocuments, type DocumentItem } from '@/api/documents'
import { fetchDependencyHealth, type DependencyHealth } from '@/api/health'

const documents = ref<DocumentItem[]>([])
const messages = ref<MessageLog[]>([])
const health = ref<DependencyHealth | null>(null)
const loading = ref(true)
const errorMessage = ref('')
const todayCount = computed(() => {
  const today = new Date().toDateString()
  return messages.value.filter(
    (item) => item.role === 'user' && new Date(item.created_at).toDateString() === today,
  ).length
})
const failedCount = computed(() => messages.value.filter((item) => item.status === 'failed').length)

onMounted(async () => {
  try {
    ;[documents.value, messages.value, health.value] = await Promise.all([
      listDocuments(),
      listMessages(),
      fetchDependencyHealth(),
    ])
  } catch (error: unknown) {
    errorMessage.value = error instanceof Error ? error.message : '加载失败'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <el-alert v-if="errorMessage" :title="errorMessage" type="error" show-icon :closable="false" />
  <el-row :gutter="20" v-loading="loading">
    <el-col :xs="24" :md="12" :xl="6"><el-card shadow="never"><template #header>知识库文档</template><div class="metric">{{ documents.length }}</div><p class="metric-note">{{ documents.filter((item) => item.status === 'indexed').length }} 份已完成索引</p></el-card></el-col>
    <el-col :xs="24" :md="12" :xl="6"><el-card shadow="never"><template #header>今日提问</template><div class="metric">{{ todayCount }}</div><p class="metric-note">Web 与钉钉统一统计</p></el-card></el-col>
    <el-col :xs="24" :md="12" :xl="6"><el-card shadow="never"><template #header>失败回答</template><div class="metric">{{ failedCount }}</div><p class="metric-note">可在对话日志定位</p></el-card></el-col>
    <el-col :xs="24" :md="12" :xl="6"><el-card shadow="never"><template #header>系统状态</template><div class="metric metric-status">{{ health?.status === 'ok' ? '在线' : '离线' }}</div><p class="metric-note">数据库 {{ health?.database ?? '检查中' }}</p></el-card></el-col>
  </el-row>
  <el-card shadow="never" class="section-card">
    <template #header>接入检查</template>
    <el-descriptions :column="2" border>
      <el-descriptions-item label="对话模型">{{ health?.llm_model ?? '-' }}</el-descriptions-item>
      <el-descriptions-item label="向量模型">{{ health?.embedding_model ?? '-' }}</el-descriptions-item>
      <el-descriptions-item label="向量维度">{{ health?.embedding_dimension ?? '-' }}</el-descriptions-item>
      <el-descriptions-item label="API Key"><el-tag :type="health?.model_api_key_configured ? 'success' : 'warning'">{{ health?.model_api_key_configured ? '已配置' : '待填写' }}</el-tag></el-descriptions-item>
    </el-descriptions>
  </el-card>
</template>
