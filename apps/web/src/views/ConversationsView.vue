<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { listMessages, type MessageLog } from '@/api/admin'

const messages = ref<MessageLog[]>([])
const loading = ref(true)
const platform = ref('')
const failedOnly = ref(false)
const filtered = computed(() =>
  messages.value.filter(
    (item) =>
      (!platform.value || item.platform === platform.value) &&
      (!failedOnly.value || item.status === 'failed'),
  ),
)
onMounted(async () => {
  try {
    messages.value = await listMessages(500)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <el-card shadow="never">
    <div class="toolbar">
      <div><strong>用户问答记录</strong><p>工具参数和结果、引用、Token、成本与错误均随回答保存。</p></div>
      <div class="filters">
        <el-select v-model="platform" clearable placeholder="全部来源" style="width: 130px">
          <el-option label="Web" value="web" /><el-option label="钉钉" value="dingtalk" />
        </el-select>
        <el-checkbox v-model="failedOnly">只看失败</el-checkbox>
      </div>
    </div>
    <el-table :data="filtered" v-loading="loading" row-key="id">
      <el-table-column type="expand">
        <template #default="scope">
          <div class="log-detail">
            <h4>完整内容</h4><p>{{ scope.row.content }}</p>
            <h4 v-if="scope.row.tool_calls.length">工具调用</h4>
            <pre v-if="scope.row.tool_calls.length">{{ JSON.stringify(scope.row.tool_calls, null, 2) }}</pre>
            <h4 v-if="scope.row.citations.length">引用</h4>
            <pre v-if="scope.row.citations.length">{{ JSON.stringify(scope.row.citations, null, 2) }}</pre>
            <p v-if="scope.row.error_code" class="error-text">错误：{{ scope.row.error_code }}</p>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="时间" width="180"><template #default="scope">{{ new Date(scope.row.created_at).toLocaleString() }}</template></el-table-column>
      <el-table-column label="来源" width="90"><template #default="scope"><el-tag effect="plain">{{ scope.row.platform }}</el-tag></template></el-table-column>
      <el-table-column label="用户" width="130"><template #default="scope">{{ scope.row.user_name ?? scope.row.external_user_id }}</template></el-table-column>
      <el-table-column label="角色" prop="role" width="90" />
      <el-table-column label="内容" prop="content" min-width="280" show-overflow-tooltip />
      <el-table-column label="工具" width="80"><template #default="scope">{{ scope.row.tool_calls.length }}</template></el-table-column>
      <el-table-column label="Token" width="100"><template #default="scope">{{ scope.row.prompt_tokens + scope.row.completion_tokens }}</template></el-table-column>
      <el-table-column label="成本" width="100"><template #default="scope">¥{{ scope.row.cost.toFixed(6) }}</template></el-table-column>
      <el-table-column label="耗时" width="90"><template #default="scope">{{ scope.row.latency_ms }}ms</template></el-table-column>
      <el-table-column label="状态" width="100"><template #default="scope"><el-tag :type="scope.row.status === 'completed' ? 'success' : 'danger'">{{ scope.row.status }}</el-tag></template></el-table-column>
    </el-table>
  </el-card>
</template>
