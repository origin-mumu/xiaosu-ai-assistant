import { apiRequest, jsonRequest } from './client'

export interface AdminSession {
  username: string
}

export function login(username: string, password: string): Promise<AdminSession> {
  return apiRequest('/auth/login', jsonRequest('POST', { username, password }))
}

export function currentSession(): Promise<AdminSession> {
  return apiRequest('/auth/me')
}

export function logout(): Promise<void> {
  return apiRequest('/auth/logout', { method: 'POST' })
}
