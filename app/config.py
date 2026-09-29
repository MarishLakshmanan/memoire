"""Environment configuration for the application."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Runtime configuration resolved from the environment.

    Args:
        clerk_issuer (str): Clerk instance URL that issues tokens, with no trailing slash.
        resource_url (str): This server's RFC 8707 resource identifier, matched against token `aud`.
        is_production (bool): True when running in production, which turns audience checking on.
        clerk_public_key (str): PEM-encoded RSA public key used to verify token signatures.
        database_url (str): `postgresql+asyncpg://` connection string.
        cors_origins (list[str]): Origins allowed to call the /api routes from a browser.
    """

    clerk_issuer: str
    resource_url: str
    is_production: bool
    clerk_public_key: str
    database_url: str
    cors_origins: list[str]


def load_settings() -> Settings:
    """Read and validate the application's configuration from environment variables.

    Returns:
        Settings: The validated configuration.

    Raises:
        ValueError: If APP_ENV is not "development" or "production", or if a required
            variable is missing.
    """
    app_env = os.getenv("APP_ENV", "development")
    if app_env not in ("development", "production"):
        raise ValueError(f'APP_ENV must be "development" or "production", got {app_env!r}')

    issuer = os.getenv("CLERK_ISSUER")
    if not issuer:
        raise ValueError("CLERK_ISSUER is required (e.g. https://your-app.clerk.accounts.dev)")

    resource_url = os.getenv("MCP_RESOURCE_URL")
    if not resource_url:
        raise ValueError("MCP_RESOURCE_URL is required (e.g. http://localhost:8000/mcp)")

    key_path = Path(os.getenv("CLERK_PUBLIC_KEY_PATH", "clerk.pem"))
    if not key_path.is_file():
        raise ValueError(
            f"Clerk public key not found at {key_path}. Download it from the Clerk dashboard."
        )

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError(
            "DATABASE_URL is required (e.g. postgresql+asyncpg://user:pass@localhost:5433/ai_notes)"
        )

    cors_origins_raw = os.getenv("CORS_ORIGINS")
    if cors_origins_raw:
        cors_origins = [origin.strip() for origin in cors_origins_raw.split(",") if origin.strip()]
    elif app_env == "development":
        cors_origins = ["http://localhost:5173"]
    else:
        raise ValueError("CORS_ORIGINS is required in production (comma-separated origins).")

    return Settings(
        clerk_issuer=issuer.rstrip("/"),
        resource_url=resource_url,
        is_production=app_env == "production",
        clerk_public_key=key_path.read_text(),
        database_url=database_url,
        cors_origins=cors_origins,
    )
