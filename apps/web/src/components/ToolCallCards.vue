<script setup lang="ts">
import { computed } from 'vue'

import type { Citation } from '@/api/documents'

const props = defineProps<{
  toolCalls: Array<Record<string, unknown>>
  citations: Citation[]
}>()

const emit = defineEmits<{
  openCitation: [citation: Citation]
}>()

const toolNames: Record<string, string> = {
  search_knowledge: '知识库检索',
  find_employee: '员工姓名查询',
  get_employee: '员工信息查询',
  query_attendance: '考勤记录查询',
  query_orders: '订单数据汇总',
  get_current_time: '当前时间查询',
}

const displayCalls = computed(() => {
  if (!props.citations.length || props.toolCalls.some((call) => call.name === 'search_knowledge')) {
    return props.toolCalls
  }
  return [
    ...props.toolCalls,
    {
      name: 'search_knowledge',
      arguments: {},
      result: { found: true, matches: props.citations },
      success: true,
    },
  ]
})

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === 'object' && !Array.isArray(value)
    ? value as Record<string, unknown>
    : {}
}

function shortText(value: unknown, fallback = '未提供'): string {
  const text = String(value ?? '').trim()
  if (!text) return fallback
  return text.length > 70 ? `${text.slice(0, 70)}…` : text
}

function displayName(call: Record<string, unknown>): string {
  return toolNames[String(call.name)] ?? '内部工具'
}

function toolAction(call: Record<string, unknown>): string {
  const name = String(call.name ?? '')
  const args = asRecord(call.arguments)
  if (name === 'search_knowledge') return `检索“${shortText(args.query, '当前问题')}”相关的知识库内容`
  if (name === 'find_employee') return `按姓名“${shortText(args.name)}”查找员工信息`
  if (name === 'get_employee') return `查询员工 ${shortText(args.employee_id)} 的部门、职级和在职状态`
  if (name === 'query_attendance') return `查询员工 ${shortText(args.employee_id)} 在 ${shortText(args.start_date)} 至 ${shortText(args.end_date)} 的考勤`
  if (name === 'query_orders') return `汇总 ${shortText(args.start_date)} 至 ${shortText(args.end_date)} 的订单数据`
  if (name === 'get_current_time') return `查询 ${shortText(args.timezone, 'Asia/Shanghai')} 的当前时间`
  return '根据当前问题查询所需业务数据'
}

function toolOutcome(call: Record<string, unknown>): string {
  const name = String(call.name ?? '')
  const result = asRecord(call.result)
  if (result.error) return `查询失败：${shortText(result.error)}`
  if (name === 'search_knowledge') {
    const matches = Array.isArray(result.matches) ? result.matches : []
    const count = props.citations.length || matches.length
    const filenames = [...new Set(
      (props.citations.length ? props.citations : matches)
        .map((item) => String(asRecord(item).filename ?? ''))
        .filter(Boolean),
    )]
    return count
      ? `找到 ${count} 条相关原文${filenames.length ? `，来自 ${filenames.slice(0, 3).join('、')}` : ''}`
      : '没有找到达到相似度要求的原文'
  }
  if (name === 'get_employee') {
    const employee = asRecord(result.employee)
    return result.found
      ? `查到 ${shortText(employee.name)}，${shortText(employee.dept)}，职级 ${shortText(employee.level)}`
      : '未找到该员工'
  }
  if (name === 'find_employee') {
    const employees = Array.isArray(result.employees) ? result.employees : []
    const names = employees.map((item) => shortText(asRecord(item).name)).slice(0, 4)
    return employees.length ? `找到 ${employees.length} 位员工：${names.join('、')}` : '未找到匹配员工'
  }
  if (name === 'query_attendance') {
    const summary = asRecord(result.summary)
    return `应出勤 ${shortText(summary.scheduled_days, '0')} 天，实到 ${shortText(summary.present_days, '0')} 天，迟到 ${shortText(summary.late_days, '0')} 天，请假 ${shortText(summary.leave_days, '0')} 天`
  }
  if (name === 'query_orders') {
    const summary = asRecord(result.summary)
    return `共 ${shortText(summary.order_count, '0')} 笔订单，销售额 ¥${shortText(summary.gross_amount, '0')}，净销售额 ¥${shortText(summary.net_amount, '0')}`
  }
  if (name === 'get_current_time') return `当前时间：${shortText(result.datetime)}`
  return result.found === false ? '未找到匹配数据' : '查询完成，已返回可用结果'
}

function succeeded(call: Record<string, unknown>): boolean {
  return call.success !== false && !asRecord(call.result).error
}
</script>

<template>
  <section v-if="displayCalls.length" class="tool-card-stack">
    <template v-for="(call, index) in displayCalls" :key="`${String(call.name)}-${index}`">
      <details v-if="call.name === 'search_knowledge'" class="tool-result-card knowledge-tool-card">
        <summary>
          <span class="tool-order">{{ index + 1 }}</span>
          <span class="tool-card-heading">
            <strong>{{ displayName(call) }}</strong>
            <small>{{ toolOutcome(call) }}</small>
          </span>
          <el-tag :type="succeeded(call) ? 'success' : 'danger'" effect="light" size="small">
            {{ succeeded(call) ? '完成' : '失败' }}
          </el-tag>
          <span class="tool-expand-label">{{ citations.length }} 条引用</span>
        </summary>
        <div class="tool-card-body">
          <dl>
            <div><dt>做了什么</dt><dd>{{ toolAction(call) }}</dd></div>
            <div><dt>查到什么</dt><dd>{{ toolOutcome(call) }}</dd></div>
          </dl>
          <div v-if="citations.length" class="tool-citation-list">
            <button
              v-for="citation in citations"
              :key="citation.chunk_id"
              type="button"
              @click="emit('openCitation', citation)"
            >
              <span><strong>{{ citation.filename }}</strong><em>{{ citation.section_title ?? (citation.page_number ? `第 ${citation.page_number} 页` : `第 ${citation.paragraph_start ?? '-'} 段`) }}</em></span>
              <small>{{ citation.content }}</small>
              <i>预览并定位 →</i>
            </button>
          </div>
        </div>
      </details>

      <article v-else class="tool-result-card">
        <header>
          <span class="tool-order">{{ index + 1 }}</span>
          <strong>{{ displayName(call) }}</strong>
          <el-tag :type="succeeded(call) ? 'success' : 'danger'" effect="light" size="small">
            {{ succeeded(call) ? '完成' : '失败' }}
          </el-tag>
        </header>
        <dl>
          <div><dt>做了什么</dt><dd>{{ toolAction(call) }}</dd></div>
          <div><dt>查到什么</dt><dd>{{ toolOutcome(call) }}</dd></div>
        </dl>
      </article>
    </template>
  </section>
</template>
