export interface HealthResponse {
  status: string
  service: string
  timestamp: string
}

export interface DependencyHealth {
  status: string
  database: string
  llm_provider: string
  llm_model: string
  embedding_model: string
  embedding_dimension: number
  model_api_key_configured: boolean
}

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch('/api/v1/health')

  if (!response.ok) {
    throw new Error('后端健康检查失败')
  }

  return (await response.json()) as HealthResponse
}

export async function fetchDependencyHealth(): Promise<DependencyHealth> {
  const response = await fetch('/api/v1/health/dependencies')
  if (!response.ok) throw new Error('依赖健康检查失败')
  return (await response.json()) as DependencyHealth
}
