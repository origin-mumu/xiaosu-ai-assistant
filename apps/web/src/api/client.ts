export async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(`/api/v1${path}`, { credentials: 'same-origin', ...init })
  } catch (error: unknown) {
    throw new Error(
      error instanceof Error && (error.message === 'Failed to fetch' || error.name === 'TypeError')
        ? '无法连接后端服务，请检查 API 容器运行状态与端口网络'
        : error instanceof Error
          ? error.message
          : '网络请求异常，请稍后重试',
    )
  }
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { detail?: string } | null
    if (response.status === 401 && !path.startsWith('/auth/')) {
      window.dispatchEvent(new Event('xiaosu:unauthorized'))
    }
    throw new Error(body?.detail ?? `请求失败（HTTP ${response.status}）`)
  }
  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}

export function jsonRequest(method: string, body: unknown): RequestInit {
  return {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }
}
