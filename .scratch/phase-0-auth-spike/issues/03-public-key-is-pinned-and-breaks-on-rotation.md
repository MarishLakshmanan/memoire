# Pinned public key breaks when Clerk rotates signing keys

Status: open

Token signatures are verified against a single PEM read from `clerk.pem` at startup. This is
simple and needs no network call, but it pins one signing key: when Clerk rotates, every token
fails verification until someone downloads a new PEM and restarts. The failure looks like a
total auth outage with no obvious cause.

The alternative is fetching Clerk's JWKS (`{issuer}/.well-known/jwks.json`) with a caching
client, which follows rotation automatically at the cost of a network dependency and a
blocking fetch that needs offloading off the event loop.

## Decision needed before production

The PEM is fine for the spike and for local development. Decide before deploying whether to
switch to JWKS, and if the PEM stays, document who re-downloads it and how rotation is noticed.
