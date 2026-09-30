import { ClerkProvider, SignedIn, SignedOut, SignInButton, UserButton } from '@clerk/clerk-react'
import { Link, Route, BrowserRouter as Router, Routes } from 'react-router-dom'
import Home from './pages/Home'
import NotebookDetailPage from './pages/NotebookDetail'

const PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY

if (!PUBLISHABLE_KEY) {
  throw new Error('Missing VITE_CLERK_PUBLISHABLE_KEY — copy frontend/.env.example to frontend/.env')
}

export default function App() {
  return (
    <ClerkProvider publishableKey={PUBLISHABLE_KEY}>
      <Router>
        <header className="flex items-center justify-between border-b border-gray-200 px-4 py-3">
          <Link to="/" className="text-lg font-semibold">
            mémoire
          </Link>
          <SignedIn>
            <UserButton />
          </SignedIn>
          <SignedOut>
            <SignInButton mode="modal" />
          </SignedOut>
        </header>

        <SignedIn>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/notebooks/:id" element={<NotebookDetailPage />} />
          </Routes>
        </SignedIn>
        <SignedOut>
          <p className="mx-auto max-w-3xl px-4 py-10 text-gray-500">Sign in to see your notebooks.</p>
        </SignedOut>
      </Router>
    </ClerkProvider>
  )
}
