<script setup lang="ts">
import { Connection, Cpu } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { computed, onMounted, ref } from 'vue'

import { fetchSettings, updateModel, type SystemSettings } from '@/api/admin'

const settings = ref<SystemSettings | null>(null)
const loading = ref(true)
const saving = ref(false)
const provider = ref<string>('dashscope')
const modelName = ref('')

const currentProviderOptions = computed(() => {
  if (!settings.value?.providers_info) return settings.value?.llm_model_options ?? []
  const info = settings.value.providers_info[provider.value]
  return info?.models ?? settings.value.llm_model_options ?? []
})

const isDirty = computed(() => {
  if (!settings.value) return false
  return provider.value !== settings.value.llm_provider || modelName.value !== settings.value.llm_model
})

function onProviderChange(newProvider: unknown): void {
  const p = String(newProvider ?? 'dashscope')
  const info = settings.value?.providers_info?.[p]
  if (info?.models?.length && info.models[0]) {
    modelName.value = info.models[0]
  }
}

function formatTime(value: string | null | undefined): string {
  return value ? new Date(value).toLocaleString() : '暂无心跳'
}

async function refresh(): Promise<void> {
  loading.value = true
  try {
    settings.value = await fetchSettings()
    if (settings.value) {
      provider.value = settings.value.llm_provider ?? 'dashscope'
      modelName.value = settings.value.llm_model ?? ''
    }
  } finally {
    loading.value = false
  }
}

async function saveModel(): Promise<void> {
  if (!modelName.value.trim()) return
  saving.value = true
  try {
    const result = await updateModel(modelName.value.trim(), provider.value)
    if (settings.value) {
      settings.value.llm_provider = result.llm_provider
      settings.value.llm_model = result.llm_model
    }
    ElMessage.success('模型与供应商已持久化切换，Web 调试与钉钉下一次对话起生效')
    await refresh()
  } finally {
    saving.value = false
  }
}

onMounted(refresh)
</script>

<template>
  <div v-loading="loading" class="settings-page-grid">
    <el-card shadow="never" class="model-switch-card">
      <template #header>
        <div class="settings-card-heading">
          <span class="settings-card-icon"><el-icon><Cpu /></el-icon></span>
          <div><strong>对话模型与供应商切换</strong><small>支持阿里百炼与智谱清言多厂商热切换</small></div>
        </div>
      </template>
      <div class="model-switch-panel">
        <div class="model-form-item">
          <label>模型供应商</label>
          <el-radio-group v-model="provider" @change="onProviderChange">
            <el-radio-button value="dashscope">阿里百炼 (DashScope)</el-radio-button>
            <el-radio-button value="zhipuai">智谱清言 (ZhipuAI)</el-radio-button>
          </el-radio-group>
        </div>

        <div class="model-form-item">
          <label>对话大模型</label>
          <div class="model-switch-control">
            <el-select
              v-model="modelName"
              filterable
              allow-create
              default-first-option
              placeholder="选择或输入模型名称"
            >
              <el-option
                v-for="model in currentProviderOptions"
                :key="model"
                :label="model"
                :value="model"
              />
            </el-select>
            <el-button
              type="primary"
              :disabled="!isDirty"
              :loading="saving"
              @click="saveModel"
            >应用配置</el-button>
          </div>
        </div>

        <div class="active-model-row">
          <span><i></i>当前生效：<strong>{{ settings?.llm_provider }} · {{ settings?.llm_model }}</strong></span>
          <el-tag type="success" effect="light">数据库持久化</el-tag>
        </div>
      </div>

      <el-descriptions :column="1" border>
        <el-descriptions-item label="当前供应商">
          {{ settings?.llm_provider === 'zhipuai' ? '智谱清言 (ZhipuAI)' : '阿里百炼 (DashScope)' }}
        </el-descriptions-item>
        <el-descriptions-item label="Embedding 向量模型">
          {{ settings?.embedding_model }}（{{ settings?.embedding_dimension }} 维）
        </el-descriptions-item>
        <el-descriptions-item label="阿里百炼 API Key">
          <el-tag :type="settings?.dashscope_configured ? 'success' : 'warning'">
            {{ settings?.dashscope_configured ? '已配置' : '待配置 (DASHSCOPE_API_KEY)' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="智谱清言 API Key">
          <el-tag :type="settings?.zhipuai_configured ? 'success' : 'warning'">
            {{ settings?.zhipuai_configured ? '已配置' : '待配置 (ZHIPUAI_API_KEY)' }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card shadow="never" class="im-status-card">
      <template #header>
        <div class="settings-card-heading">
          <span class="settings-card-icon green"><el-icon><Connection /></el-icon></span>
          <div><strong>IM 接入状态</strong><small>查看终端员工使用的钉钉 Stream 通道</small></div>
        </div>
      </template>
      <div class="im-runtime-status" :class="{ connected: settings?.im_status.connected }">
        <span class="im-status-dot"></span>
        <div>
          <strong>{{ settings?.im_status.status ?? '检查中' }}</strong>
          <small>
            {{ settings?.im_status.connected ? '钉钉机器人心跳正常，可接收员工消息' : '请检查凭证和机器人进程' }}
          </small>
        </div>
      </div>
      <el-descriptions :column="1" border>
        <el-descriptions-item label="接入渠道">钉钉 Stream</el-descriptions-item>
        <el-descriptions-item label="接入凭证">
          <el-tag :type="settings?.dingtalk_configured ? 'success' : 'warning'">
            {{ settings?.dingtalk_configured ? '已配置' : '待配置' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="服务状态">
          <el-tag :type="settings?.im_status.connected ? 'success' : 'danger'">
            {{ settings?.im_status.status ?? '未知' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="最近心跳">
          {{ formatTime(settings?.im_status.last_heartbeat_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="当前检索配置">
          Top K {{ settings?.retrieval_top_k }} · 最低相似度 {{ settings?.retrieval_min_score }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>

  <el-alert
    class="section-card"
    title="密钥仅通过环境变量配置，不会在后台明文展示"
    description="模型供应商与模型名称保存在数据库；API Key、钉钉 Client ID 和 Client Secret 仍通过 .env 管理。"
    type="info"
    show-icon
    :closable="false"
  />
</template>

<style scoped>
.model-form-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}
.model-form-item > label {
  font-size: 13px;
  font-weight: 500;
  color: var(--el-text-color-regular);
}
</style>
