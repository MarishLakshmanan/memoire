# Transport security is left at localhost defaults

Status: open

`streamable_http_app()` binds to `127.0.0.1` and applies DNS-rebinding protection with default
allowed hosts. That is correct for local development and wrong for a deployed server: requests
arriving with the production hostname will be refused.

Before deploying, pass `TransportSecuritySettings` with an explicit `allowed_hosts` and
`allowed_origins` for the real domain.

Also relevant for the web frontend in phase 4: browser clients need CORS configured to allow
`Mcp-*` request headers and to expose `Mcp-Session-Id`.
