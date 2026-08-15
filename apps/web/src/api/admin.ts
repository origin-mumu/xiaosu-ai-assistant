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

export interface SystemSettings {
  llm_provider: string
  llm_model: string
  embedding_model: string
  embedding_dimension: number
  model_api_key_configured: boolean
  dingtalk_configured: boolean
  retrieval_top_k: number
  retrieval_min_score: number
}

export function listMessages(limit = 200): Promise<MessageLog[]> {
  return apiRequest(`/admin/messages?limit=${limit}`)
}

export function fetchSettings(): Promise<SystemSettings> {
  return apiRequest('/admin/settings')
}

export function updateModel(llmModel: string): Promise<{ llm_model: string; persistence: string }> {
  return apiRequest('/admin/settings', jsonRequest('PATCH', { llm_model: llmModel }))
}
