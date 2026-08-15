<script setup lang="ts">
import { Promotion } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { nextTick, ref } from 'vue'

import { streamChat, type ChatResult, type StreamEvent } from '@/api/chat'

interface ProgressStep {
  stage: string
  label: string
  complete: boolean
}

interface DisplayMessage {
  role: 'user' | 'assistant'
  content: string
  result?: ChatResult
  progress?: ProgressStep[]
}

const input = ref('')
const sending = ref(false)
const messages = ref<DisplayMessage[]>([])
const conversationId = sessionStorage.getItem('xiaosu-conversation') ?? crypto.randomUUID()
sessionStorage.setItem('xiaosu-conversation', conversationId)

async function send(): Promise<void> {
  const content = input.value.trim()
  if (!content || sending.value) return
  input.value = ''
  messages.value.push({ role: 'user', content })
  const assistant: DisplayMessage = { role: 'assistant', content: '', progress: [] }
  messages.value.push(assistant)
  sending.value = true
  try {
    assistant.result = await streamChat(
      {
        message: content,
        platform: 'web',
        tenant_id: 'default',
        conversation_id: conversationId,
        user_id: 'admin',
        user_name: '管理员',
      },
      (event: StreamEvent) => {
        if (event.type === 'status' && event.stage && event.label) {
          const previous = assistant.progress?.[assistant.progress.length - 1]
          if (previous) previous.complete = true
          if (!previous || previous.stage !== event.stage || previous.label !== event.label) {
            assistant.progress?.push({
              stage: event.stage,
              label: event.label,
              complete: false,
            })
          }
        }
        if (event.type === 'delta' && event.content) {
          const current = assistant.progress?.[assistant.progress.length - 1]
          if (current) current.complete = true
          assistant.content += event.content
        }
        if (event.type === 'done') {
          const current = assistant.progress?.[assistant.progress.length - 1]
          if (current) current.complete = true
        }
        void nextTick(() =>
          document
            .querySelector('.chat-list')
            ?.scrollTo({ top: 999999, behavior: 'smooth' }),
        )
      },
    )
  } catch (error: unknown) {
    assistant.content = '请求失败，请检查后端。'
    ElMessage.error(error instanceof Error ? error.message : '聊天失败')
  } finally {
    sending.value = false
  }
}
</script>

<template>
  <el-card shadow="never" class="chat-card">
    <div class="chat-list">
      <div v-if="!messages.length" class="chat-empty">
        <span class="chat-mascot"><img src="/xiaosu-mascot.png" alt="小苏" /></span>
        <h2>你好，我是小苏</h2>
        <p>试试问：员工 001 是哪个部门的？／上周一共多少订单？／现在几点？</p>
      </div>
      <div
        v-for="(message, index) in messages"
        :key="index"
        class="chat-message"
        :class="message.role"
      >
        <div class="bubble">
          <div v-if="message.role === 'assistant' && message.progress?.length" class="answer-progress">
            <span
              v-for="(step, stepIndex) in message.progress"
              :key="`${step.stage}-${stepIndex}`"
              :class="{ complete: step.complete }"
            >
              <i></i>{{ step.label }}
            </span>
          </div>
          {{ message.content }}
          <div v-if="message.result" class="answer-meta">
            <span>{{ message.result.prompt_tokens + message.result.completion_tokens }} Token</span>
            <span>¥{{ message.result.cost.toFixed(6) }}</span>
            <span>{{ message.result.latency_ms }}ms</span>
            <span>{{ message.result.tool_calls.length }} 个工具</span>
          </div>
          <div v-if="message.result?.citations.length" class="citation-list">
            <router-link
              v-for="citation in message.result.citations"
              :key="citation.chunk_id"
              :to="`/documents/${citation.document_id}?chunk=${citation.chunk_id}`"
            >
              <strong>
                {{ citation.filename }} ·
                {{ citation.section_title ?? `第 ${citation.paragraph_start ?? '-'} 段` }}
              </strong>
              <small>{{ citation.content }}</small>
            </router-link>
          </div>
        </div>
      </div>
    </div>
    <div class="chat-input">
      <el-input
        v-model="input"
        type="textarea"
        :autosize="{ minRows: 1, maxRows: 4 }"
        resize="none"
        placeholder="输入问题，Enter 发送，Shift+Enter 换行"
        @keydown.enter.exact.prevent="send"
      />
      <el-button
        class="send-button"
        type="primary"
        circle
        :loading="sending"
        :disabled="!input.trim()"
        aria-label="发送消息"
        title="发送"
        @click="send"
      ><el-icon><Promotion /></el-icon></el-button>
    </div>
  </el-card>
</template>
