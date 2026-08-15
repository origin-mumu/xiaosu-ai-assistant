import type { Citation } from './documents'

export interface ChatRequest {
  message: string
  platform: 'web'
  tenant_id: string
  conversation_id: string
  user_id: string
  user_name?: string
}

export interface ChatResult {
  conversation_uuid: string
  message_id: string
  answer: string
  citations: Citation[]
  tool_calls: Array<Record<string, unknown>>
  prompt_tokens: number
  completion_tokens: number
  cost: number
  latency_ms: number
  status: string
}

interface StreamEvent {
  type: 'delta' | 'done'
  content?: string
  data?: ChatResult
}

export async function streamChat(
  request: ChatRequest,
  onDelta: (content: string) => void,
): Promise<ChatResult> {
  const response = await fetch('/api/v1/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })
  if (!response.ok || !response.body) throw new Error('无法连接聊天服务')
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let result: ChatResult | undefined
  while (true) {
    const { value, done } = await reader.read()
    buffer += decoder.decode(value, { stream: !done })
    const blocks = buffer.split('\n\n')
    buffer = blocks.pop() ?? ''
    for (const block of blocks) {
      const line = block.split('\n').find((item) => item.startsWith('data: '))
      if (!line) continue
      const event = JSON.parse(line.slice(6)) as StreamEvent
      if (event.type === 'delta' && event.content) onDelta(event.content)
      if (event.type === 'done') result = event.data
    }
    if (done) break
  }
  if (!result) throw new Error('聊天流意外结束')
  return result
}
