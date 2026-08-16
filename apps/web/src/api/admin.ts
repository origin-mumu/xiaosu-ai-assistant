import { apiRequest } from './client'
import { jsonRequest } from './client'

export interface MessageLog {
  id: string
  conversation_id: string
  platform: string
  external_user_id: string
  user_name: string | null
  role: string
  content: string
  status: string
  model: string | null
  prompt_tokens: number
  completion_tokens: number
  cost: number
  latency_ms: number
  tool_calls: Array<Record<string, unknown>>
  citations: Array<Record<string, unknown>>
  error_code: string | null
  created_at: string
}

export interface MessageUserOption {
  value: string
  label: string
}

export interface QuestionAnswerLog {
  question: MessageLog
  answer: MessageLog | null
}

export interface MessagePage {
  items: QuestionAnswerLog[]
  total: number
  page: number
  page_size: number
  users: MessageUserOption[]
}

export interface MessageQuery {
  page?: number
  pageSize?: number
  platform?: string
  userId?: string
  status?: string
}

export interface ToolCallLog {
  id: string
  message_id: string
  conversation_id: string
  platform: string
  external_user_id: string
  user_name: string | null
  tool_name: string
  arguments: Record<string, unknown>
  result: unknown
  duration_ms: number | null
  success: boolean
  created_at: string
}

export interface ToolCallPage {
  items: ToolCallLog[]
  total: number
  page: number
  page_size: number
  tool_names: string[]
}

export interface ToolCallQuery {
  page?: number
  pageSize?: number
  platform?: string
  toolName?: string
  success?: boolean | ''
}

export interface ProviderInfo {
  name: string
  configured: boolean
  models: string[]
  embedding_model: string
}

export interface SystemSettings {
  llm_provider: 'dashscope' | 'zhipuai' | string
  llm_providers: string[]
  providers_info: Record<string, ProviderInfo>
  llm_model: string
  llm_model_options: string[]
  embedding_model: string
  embedding_dimension: number
  model_api_key_configured: boolean
  dashscope_configured: boolean
  zhipuai_configured: boolean
  dingtalk_configured: boolean
  retrieval_top_k: number
  retrieval_min_score: number
  chunk_size: number
  chunk_overlap: number
  max_upload_mb: number
  embedding_batch_size: number
  duplicate_policy: 'replace' | 'skip'
  im_status: {
    channel: string
    configured: boolean
    connected: boolean
    status: string
    last_heartbeat_at: string | null
  }
}

export interface ToolDefinition {
  id: string
  name: string
  description: string
  category: string
  parameters: string[]
  enabled: boolean
}

export interface KnowledgeSettingsUpdate {
  chunk_size: number
  chunk_overlap: number
  retrieval_top_k: number
  retrieval_min_score: number
  max_upload_mb: number
  embedding_batch_size: number
  duplicate_policy: 'replace' | 'skip'
}

export function listMessages(query: MessageQuery = {}): Promise<MessagePage> {
  const params = new URLSearchParams({
    page: String(query.page ?? 1),
    page_size: String(query.pageSize ?? 200),
  })
  if (query.platform) params.set('platform', query.platform)
  if (query.userId) params.set('user_id', query.userId)
  if (query.status) params.set('status', query.status)
  return apiRequest(`/admin/messages?${params.toString()}`)
}

export function listToolCalls(query: ToolCallQuery = {}): Promise<ToolCallPage> {
  const params = new URLSearchParams({
    page: String(query.page ?? 1),
    page_size: String(query.pageSize ?? 20),
  })
  if (query.platform) params.set('platform', query.platform)
  if (query.toolName) params.set('tool_name', query.toolName)
  if (query.success !== '' && query.success !== undefined) {
    params.set('success', String(query.success))
  }
  return apiRequest(`/admin/tool-calls?${params.toString()}`)
}

export function fetchToolCatalog(): Promise<ToolDefinition[]> {
  return apiRequest('/admin/tools')
}

export function fetchSettings(): Promise<SystemSettings> {
  return apiRequest('/admin/settings')
}

export function updateModel(
  llmModel: string,
  llmProvider?: string,
): Promise<{ llm_provider: string; llm_model: string; persistence: string }> {
  return apiRequest('/admin/settings', jsonRequest('PATCH', {
    llm_model: llmModel,
    llm_provider: llmProvider,
  }))
}

export function updateKnowledgeSettings(
  settings: KnowledgeSettingsUpdate,
): Promise<KnowledgeSettingsUpdate & { persistence: string }> {
  return apiRequest('/admin/settings/knowledge', jsonRequest('PATCH', settings))
}
