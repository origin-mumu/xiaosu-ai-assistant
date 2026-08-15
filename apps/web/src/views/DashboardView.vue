<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { fetchHealth, type HealthResponse } from '@/api/health'

const health = ref<HealthResponse | null>(null)
const loading = ref(true)
const errorMessage = ref('')

const serviceOnline = computed(() => health.value?.status === 'ok')

onMounted(async () => {
  try {
    health.value = await fetchHealth()
  } catch (error: unknown) {
    errorMessage.value = error instanceof Error ? error.message : '未知错误'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <el-container class="app-shell">
    <el-aside width="232px" class="app-sidebar">
      <div class="brand">
        <span class="brand-mark">苏</span>
        <div>
          <strong>小苏</strong>
          <small>企业智能助手</small>
        </div>
      </div>

      <el-menu default-active="/dashboard" router>
        <el-menu-item index="/dashboard">系统概览</el-menu-item>
        <el-menu-item index="/documents" disabled>文档管理</el-menu-item>
        <el-menu-item index="/conversations" disabled>对话日志</el-menu-item>
        <el-menu-item index="/settings" disabled>系统设置</el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="app-header">
        <div>
          <h1>系统概览</h1>
          <p>小苏企业智能助手管理后台</p>
        </div>
        <el-tag :type="serviceOnline ? 'success' : 'danger'" effect="light">
          {{ serviceOnline ? 'API 正常' : 'API 未连接' }}
        </el-tag>
      </el-header>

      <el-main class="app-main">
        <el-alert
          v-if="errorMessage"
          :title="errorMessage"
          type="error"
          show-icon
          :closable="false"
        />

        <el-row :gutter="20" v-loading="loading">
          <el-col :xs="24" :md="8">
            <el-card shadow="never">
              <template #header>知识库文档</template>
              <div class="metric">0</div>
              <p class="metric-note">等待上传首份文档</p>
            </el-card>
          </el-col>
          <el-col :xs="24" :md="8">
            <el-card shadow="never">
              <template #header>今日对话</template>
              <div class="metric">0</div>
              <p class="metric-note">钉钉接入后开始统计</p>
            </el-card>
          </el-col>
          <el-col :xs="24" :md="8">
            <el-card shadow="never">
              <template #header>服务状态</template>
              <div class="metric metric-status">{{ serviceOnline ? '在线' : '离线' }}</div>
              <p class="metric-note">{{ health?.service ?? 'xiaosu-api' }}</p>
            </el-card>
          </el-col>
        </el-row>
      </el-main>
    </el-container>
  </el-container>
</template>

