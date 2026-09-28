# .env uses the Next.js publishable key prefix, not Vite's

Status: open

`.env` defines `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`, which is the Next.js convention. The
frontend is React + Vite, which only exposes variables prefixed `VITE_` to client code.

Left as is, the key reads as `undefined` in the browser and Clerk fails to initialise with no
obvious link back to the variable name.

Rename to `VITE_CLERK_PUBLISHABLE_KEY` before phase 4. `CLERK_SECRET_KEY` is correct as is and
must stay server-side only.
