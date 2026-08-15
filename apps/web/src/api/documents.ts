import { apiRequest, jsonRequest } from './client'

export interface DocumentItem {
  id: string
  filename: string
  mime_type: string
  content_hash: string
  size_bytes: number
  status: string
  error_message: string | null
  chunk_count: number
  version: number
  created_at: string
  updated_at: string
}

export interface DocumentChunk {
  id: string
  chunk_index: number
  section_title: string | null
  page_number: number | null
  paragraph_start: number | null
  paragraph_end: number | null
  content: string
}

export interface Citation {
  chunk_id: string
  document_id: string
  filename: string
  section_title: string | null
  page_number: number | null
  paragraph_start: number | null
  paragraph_end: number | null
  content: string
  score: number
}

export function listDocuments(): Promise<DocumentItem[]> {
  return apiRequest('/documents')
}

export function uploadDocument(file: File): Promise<{ action: string; document: DocumentItem }> {
  const form = new FormData()
  form.append('file', file)
  return apiRequest('/documents', { method: 'POST', body: form })
}

export function deleteDocument(id: string): Promise<void> {
  return apiRequest(`/documents/${id}`, { method: 'DELETE' })
}

export function reindexDocument(id: string): Promise<DocumentItem> {
  return apiRequest(`/documents/${id}/reindex`, { method: 'POST' })
}

export function listChunks(id: string): Promise<DocumentChunk[]> {
  return apiRequest(`/documents/${id}/chunks`)
}

export function searchKnowledge(query: string): Promise<{ citations: Citation[] }> {
  return apiRequest('/documents/search/query', jsonRequest('POST', { query, limit: 5 }))
}
