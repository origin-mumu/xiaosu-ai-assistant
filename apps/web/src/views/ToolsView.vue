<script setup lang="ts">
import { Connection } from '@element-plus/icons-vue'
import { onMounted, ref } from 'vue'

import { fetchToolCatalog, type ToolDefinition } from '@/api/admin'

const tools = ref<ToolDefinition[]>([])
const loading = ref(true)

onMounted(async () => {
  try {
    tools.value = await fetchToolCatalog()
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <el-card shadow="never">
    <div class="toolbar">
      <div>
        <strong>工具列表</strong>
        <p>查看 Agent 可使用的业务能力、用途和输入信息；实际调用记录请在对话日志中查看。</p>
      </div>
      <el-tag type="success" effect="light">{{ tools.length }} 个工具已启用</el-tag>
    </div>
    <div class="tool-catalog-grid" v-loading="loading">
      <article v-for="item in tools" :key="item.id" class="tool-catalog-card">
        <header>
          <span class="tool-catalog-icon"><el-icon><Connection /></el-icon></span>
          <div>
            <strong>{{ item.name }}</strong>
            <small>{{ item.category }}</small>
          </div>
          <el-tag :type="item.enabled ? 'success' : 'info'" size="small">
            {{ item.enabled ? '已启用' : '已停用' }}
          </el-tag>
        </header>
        <p>{{ item.description }}</p>
        <footer>
          <span>需要信息</span>
          <div v-if="item.parameters.length" class="tool-parameter-list">
            <em v-for="parameter in item.parameters" :key="parameter">{{ parameter }}</em>
          </div>
          <small v-else>无必填参数</small>
        </footer>
      </article>
    </div>
  </el-card>
</template>
