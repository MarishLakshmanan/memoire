/** Types and fetch helpers for the FastAPI backend's /api routes. */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL

export interface NotebookSummary {
  id: string
  title: string
  note_count: number
  created_at: string
  has_summary: boolean
}

export interface NoteHit {
  id: string
  notebook_id: string
  title: string
  snippet: string
  tags: string[]
  source_app: string
  created_at: string
}

export interface NoteFull {
  id: string
  title: string
  summary: string
  tags: string[]
  source_app: string
  chat_link: string | null
  created_at: string
}

export interface NotebookDetail {
  id: string
  title: string
  view: string
  notes: NoteFull[]
}

/** What GET /api/notebooks is showing: a plain listing, or the results of a search. */
export type NotebookListResult =
  | { kind: 'notebooks'; items: NotebookSummary[] }
  | { kind: 'hits'; items: NoteHit[] }

async function request<T>(path: string, token: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: { ...init?.headers, Authorization: `Bearer ${token}` },
  })
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new Error(body?.detail ?? `Request failed: ${response.status}`)
  }
  if (response.status === 204) {
    return undefined as T
  }
  return response.json() as Promise<T>
}

export async function listNotebooks(token: string): Promise<NotebookListResult> {
  const items = await request<NotebookSummary[]>('/api/notebooks', token)
  return { kind: 'notebooks', items }
}

export async function searchNotes(token: string, query: string): Promise<NotebookListResult> {
  const items = await request<NoteHit[]>(`/api/notebooks?q=${encodeURIComponent(query)}`, token)
  return { kind: 'hits', items }
}

export function getNotebook(token: string, id: string): Promise<NotebookDetail> {
  return request(`/api/notebooks/${id}`, token)
}

export function deleteNotebook(token: string, id: string): Promise<void> {
  return request(`/api/notebooks/${id}`, token, { method: 'DELETE' })
}

export function deleteNote(token: string, notebookId: string, noteId: string): Promise<void> {
  return request(`/api/notebooks/${notebookId}/notes/${noteId}`, token, { method: 'DELETE' })
}
