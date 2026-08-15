<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { onMounted, ref } from 'vue'

import { fetchSettings, updateModel, type SystemSettings } from '@/api/admin'

const settings = ref<SystemSettings | null>(null)
const loading = ref(true)
const modelName = ref('')

onMounted(async () => {
  try {
    settings.value = await fetchSettings()
    modelName.value = settings.value.llm_model
  } finally {
    loading.value = false
  }
})

async function saveModel(): Promise<void> {
  const result = await updateModel(modelName.value)
  if (settings.value) settings.value.llm_model = result.llm_model
  ElMessage.success('当前 API 进程已切换模型；重启后恢复 .env 配置')
}
</script>

<template>
  <el-row :gutter="20" v-loading="loading">
    <el-col :xs="24" :lg="12">
      <el-card shadow="never">
        <template #header>千问模型</template>
        <el-descriptions :column="1" border>
          <el-descriptions-item label="供应商">{{ settings?.llm_provider }}</el-descriptions-item>
          <el-descriptions-item label="对话模型">
            <div class="inline-setting">
              <el-input v-model="modelName" placeholder="例如 qwen3.7-plus" />
              <el-button type="primary" @click="saveModel">应用</el-button>
            </div>
          </el-descriptions-item>
          <el-descriptions-item label="Embedding">
            {{ settings?.embedding_model }}（{{ settings?.embedding_dimension }} 维）
          </el-descriptions-item>
          <el-descriptions-item label="API Key">
            <el-tag :type="settings?.model_api_key_configured ? 'success' : 'warning'">
              {{ settings?.model_api_key_configured ? '已配置' : '请填写 .env' }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>
      </el-card>
    </el-col>
    <el-col :xs="24" :lg="12">
      <el-card shadow="never">
        <template #header>检索与钉钉</template>
        <el-descriptions :column="1" border>
          <el-descriptions-item label="Top K">{{ settings?.retrieval_top_k }}</el-descriptions-item>
          <el-descriptions-item label="最低相似度">
            {{ settings?.retrieval_min_score }}
          </el-descriptions-item>
          <el-descriptions-item label="钉钉 Stream">
            <el-tag :type="settings?.dingtalk_configured ? 'success' : 'info'">
              {{ settings?.dingtalk_configured ? '凭证已配置' : '待配置' }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>
      </el-card>
    </el-col>
  </el-row>
  <el-alert
    class="section-card"
    title="密钥不会在此页面展示或修改"
    description="编辑项目根目录本机 .env，填写 DASHSCOPE_API_KEY、DINGTALK_CLIENT_ID、DINGTALK_CLIENT_SECRET 后重启容器。钉钉机器人使用 docker compose --profile dingtalk up -d 启动。"
    type="info"
    show-icon
    :closable="false"
  />
</template>
