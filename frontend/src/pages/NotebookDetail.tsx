import { useAuth } from '@clerk/clerk-react'
import { useCallback, useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { deleteNote, deleteNotebook, getNotebook, type NotebookDetail } from '../api'

export default function NotebookDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { getToken } = useAuth()
  const navigate = useNavigate()
  const [notebook, setNotebook] = useState<NotebookDetail | null>(null)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    if (!id) return
    const token = await getToken()
    if (!token) return
    try {
      setNotebook(await getNotebook(token, id))
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong.')
    }
  }, [id, getToken])

  useEffect(() => {
    load()
  }, [load])

  async function handleDeleteNotebook() {
    if (!id || !window.confirm('Delete this notebook and all its notes?')) return
    const token = await getToken()
    if (!token) return
    await deleteNotebook(token, id)
    navigate('/')
  }

  async function handleDeleteNote(noteId: string) {
    if (!id || !window.confirm('Delete this note?')) return
    const token = await getToken()
    if (!token) return
    await deleteNote(token, id, noteId)
    load()
  }

  if (error) {
    return <p className="mx-auto max-w-3xl px-4 py-10 text-red-600">{error}</p>
  }

  if (!notebook) {
    return <p className="mx-auto max-w-3xl px-4 py-10 text-gray-500">Loading…</p>
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <div className="flex items-start justify-between">
        <h1 className="text-3xl font-semibold">{notebook.title}</h1>
        <button
          onClick={handleDeleteNotebook}
          className="rounded border border-red-300 px-3 py-1 text-sm text-red-600 hover:bg-red-50"
        >
          Delete notebook
        </button>
      </div>

      <pre className="mt-6 whitespace-pre-wrap font-sans text-gray-800">{notebook.view}</pre>

      <h2 className="mt-10 text-xl font-semibold">Notes</h2>
      <div className="mt-4 space-y-6">
        {notebook.notes.map((note) => (
          <div key={note.id} className="border border-gray-300 p-4">
            <div className="flex items-start justify-between">
              <h3 className="text-lg font-medium">{note.title}</h3>
              <button
                onClick={() => handleDeleteNote(note.id)}
                className="text-sm text-red-600 hover:underline"
              >
                Delete
              </button>
            </div>
            <div className="mt-1 text-sm text-gray-600">
              {new Date(note.created_at).toLocaleString()} · {note.source_app}
              {note.tags.length > 0 && ` · ${note.tags.join(', ')}`}
            </div>
            {note.chat_link && (
              <a href={note.chat_link} className="mt-1 block text-sm text-blue-600 hover:underline">
                {note.chat_link}
              </a>
            )}
            <pre className="mt-3 whitespace-pre-wrap font-sans text-gray-800">{note.summary}</pre>
          </div>
        ))}
      </div>
    </div>
  )
}
