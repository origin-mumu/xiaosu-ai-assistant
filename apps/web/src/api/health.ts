export interface HealthResponse {
  status: string
  service: string
  timestamp: string
}

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch('/api/v1/health')

  if (!response.ok) {
    throw new Error('后端健康检查失败')
  }

  return (await response.json()) as HealthResponse
}

