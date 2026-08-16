<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'

import {
  listMessages,
  type MessageLog,
  type MessageUserOption,
  type QuestionAnswerLog,
} from '@/api/admin'
import MarkdownContent from '@/components/MarkdownContent.vue'

const exchanges = ref<QuestionAnswerLog[]>([])
const loading = ref(true)
const platform = ref('')
const userId = ref('')
const statusFilter = ref('')
const users = ref<MessageUserOption[]>([])
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)

async function load(): Promise<void> {
  loading.value = true
  try {
    const result = await listMessages({
      page: page.value,
      pageSize: pageSize.value,
      platform: platform.value,
      userId: userId.value,
      status: statusFilter.value,
    })
    exchanges.value = result.items
    users.value = result.users
    total.value = result.total
  } finally {
    loading.value = false
  }
}

watch([platform, userId, statusFilter], () => {
  page.value = 1
  void load()
})
watch([page, pageSize], () => void load())
onMounted(load)

function resultOf(exchange: QuestionAnswerLog): MessageLog {
  return exchange.answer ?? exchange.question
}

function statusOf(exchange: QuestionAnswerLog): string {
  return exchange.answer?.status ?? 'unanswered'
}

const toolNames: Record<string, string> = {
  search_knowledge: '知识库检索',
  find_employee: '员工姓名查询',
  get_employee: '员工信息查询',
  query_attendance: '考勤记录查询',
  query_orders: '订单数据汇总',
  get_current_time: '当前时间查询',
}

function toolDisplayName(call: Record<string, unknown>): string {
  return toolNames[String(call.name)] ?? '内部工具'
}

function toolSucceeded(call: Record<string, unknown>): boolean {
  if (typeof call.success === 'boolean') return call.success
  return !(call.result && typeof call.result === 'object' && 'error' in call.result)
}
</script>

<template>
  <el-card shadow="never">
    <div class="toolbar">
      <div><strong>用户问答记录</strong><p>工具参数和结果、引用、Token、成本与错误均随回答保存。</p></div>
      <div class="filters">
        <el-select v-model="userId" clearable filterable placeholder="全部用户" style="width: 150px">
          <el-option v-for="user in users" :key="user.value" :label="user.label" :value="user.value" />
        </el-select>
        <el-select v-model="platform" clearable placeholder="全部来源" style="width: 130px">
          <el-option label="Web" value="web" /><el-option label="钉钉" value="dingtalk" />
        </el-select>
        <el-select v-model="statusFilter" clearable placeholder="全部状态" style="width: 140px">
          <el-option label="已回答" value="completed" />
          <el-option label="未答上" value="unanswered" />
          <el-option label="系统失败" value="failed" />
        </el-select>
      </div>
    </div>
    <div class="log-table-shell">
    <el-table
      :data="exchanges"
      v-loading="loading"
      :row-key="(row: QuestionAnswerLog) => row.question.id"
      table-layout="fixed"
    >
      <el-table-column type="expand">
        <template #default="scope">
          <div class="log-detail">
            <section class="log-detail-message question">
              <h4><span>问</span>用户问题</h4>
              <p>{{ scope.row.question.content }}</p>
            </section>
            <section class="log-detail-message answer">
              <h4><span>答</span>助手回答</h4>
              <MarkdownContent
                v-if="scope.row.answer"
                :content="scope.row.answer.content"
              />
              <p v-else class="empty-answer">暂无回答</p>
            </section>
            <section v-if="scope.row.answer?.tool_calls.length" class="conversation-audit-section">
              <h4>本次对话的工具调用</h4>
              <div class="conversation-tool-list">
                <article v-for="(call, index) in scope.row.answer.tool_calls" :key="index">
                  <header>
                    <strong>{{ toolDisplayName(call) }}</strong>
                    <el-tag :type="toolSucceeded(call) ? 'success' : 'danger'" size="small">
                      {{ toolSucceeded(call) ? '成功' : '失败' }}
                    </el-tag>
                    <small v-if="call.duration_ms !== undefined">{{ call.duration_ms }}ms</small>
                  </header>
                  <details>
                    <summary>查看调用明细</summary>
                    <div>
                      <section><span>调用参数</span><pre>{{ JSON.stringify(call.arguments, null, 2) }}</pre></section>
                      <section><span>返回结果</span><pre>{{ JSON.stringify(call.result, null, 2) }}</pre></section>
                    </div>
                  </details>
                </article>
              </div>
            </section>
            <section v-if="scope.row.answer?.citations.length" class="conversation-audit-section">
              <h4>引用来源</h4>
              <div class="conversation-citation-list">
                <router-link
                  v-for="citation in scope.row.answer.citations"
                  :key="String(citation.chunk_id)"
                  :to="`/documents/${String(citation.document_id)}?chunk=${String(citation.chunk_id)}`"
                >
                  <strong>{{ citation.filename }} · {{ citation.section_title ?? '原文片段' }}</strong>
                  <span>查看原文并定位 →</span>
                </router-link>
              </div>
            </section>
            <p v-if="resultOf(scope.row).error_code" class="error-text">错误：{{ resultOf(scope.row).error_code }}</p>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="时间" width="180"><template #default="scope">{{ new Date(scope.row.question.created_at).toLocaleString() }}</template></el-table-column>
      <el-table-column label="来源" width="90"><template #default="scope"><el-tag effect="plain">{{ scope.row.question.platform }}</el-tag></template></el-table-column>
      <el-table-column label="用户" width="130"><template #default="scope">{{ scope.row.question.user_name ?? scope.row.question.external_user_id }}</template></el-table-column>
      <el-table-column label="问答内容" min-width="430">
        <template #default="scope">
          <div class="qa-preview">
            <div class="question"><span>问</span><p>{{ scope.row.question.content }}</p></div>
            <div class="answer"><span>答</span><p>{{ scope.row.answer?.content ?? '暂无回答' }}</p></div>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="工具" width="80"><template #default="scope">{{ scope.row.answer?.tool_calls.length ?? 0 }}</template></el-table-column>
      <el-table-column label="Token" width="100"><template #default="scope">{{ resultOf(scope.row).prompt_tokens + resultOf(scope.row).completion_tokens }}</template></el-table-column>
      <el-table-column label="成本" width="100"><template #default="scope">¥{{ resultOf(scope.row).cost.toFixed(6) }}</template></el-table-column>
      <el-table-column label="耗时" width="90"><template #default="scope">{{ resultOf(scope.row).latency_ms }}ms</template></el-table-column>
      <el-table-column label="状态" width="120"><template #default="scope"><el-tag :type="statusOf(scope.row) === 'completed' ? 'success' : statusOf(scope.row) === 'unanswered' ? 'warning' : 'danger'">{{ statusOf(scope.row) }}</el-tag></template></el-table-column>
    </el-table>
    </div>
    <div class="table-pagination">
      <span>共 {{ total }} 条记录</span>
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50]"
        :total="total"
        layout="sizes, prev, pager, next"
        background
      />
    </div>
  </el-card>
</template>
