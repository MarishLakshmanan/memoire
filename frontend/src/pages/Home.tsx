import { useAuth } from '@clerk/clerk-react'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listNotebooks, searchNotes, type NoteHit, type NotebookSummary } from '../api'

export default function Home() {
  const { getToken } = useAuth()
  const [query, setQuery] = useState('')
  const [notebooks, setNotebooks] = useState<NotebookSummary[]>([])
  const [hits, setHits] = useState<NoteHit[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const trimmed = query.trim()
    let cancelled = false

    async function run() {
      const token = await getToken()
      if (!token) return
      try {
        if (trimmed) {
          const results = await searchNotes(token, trimmed)
          if (!cancelled) setHits(results)
        } else {
          const results = await listNotebooks(token)
          if (!cancelled) {
            setNotebooks(results)
            setHits(null)
          }
        }
        if (!cancelled) setError(null)
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Something went wrong.')
      }
    }

    const timeout = setTimeout(run, trimmed ? 250 : 0)
    return () => {
      cancelled = true
      clearTimeout(timeout)
    }
  }, [query, getToken])

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <input
        type="text"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        placeholder="Search…"
        className="w-full rounded bg-gray-200 px-4 py-3 text-lg text-gray-700 placeholder:text-gray-500 focus:outline-none"
      />

      {error && <p className="mt-4 text-sm text-red-600">{error}</p>}

      <ul className="mt-8 divide-y divide-gray-400 border border-gray-400">
        {hits !== null
          ? hits.map((hit) => (
              <li key={hit.id}>
                <Link to={`/notebooks/${hit.notebook_id}`} className="block px-4 py-3 hover:bg-gray-50">
                  <div className="font-medium">{hit.title}</div>
                  <div className="text-sm text-gray-600">{hit.snippet}</div>
                </Link>
              </li>
            ))
          : notebooks.map((notebook) => (
              <li key={notebook.id}>
                <Link to={`/notebooks/${notebook.id}`} className="block px-4 py-3 hover:bg-gray-50">
                  <div className="font-medium">{notebook.title}</div>
                  <div className="text-sm text-gray-600">
                    {notebook.note_count} note{notebook.note_count === 1 ? '' : 's'}
                    {notebook.has_summary ? ' · summarized' : ''}
                  </div>
                </Link>
              </li>
            ))}
        {hits === null && notebooks.length === 0 && !error && (
          <li className="px-4 py-3 text-gray-500">No notebooks yet.</li>
        )}
        {hits !== null && hits.length === 0 && !error && (
          <li className="px-4 py-3 text-gray-500">No matches.</li>
        )}
      </ul>
    </div>
  )
}
