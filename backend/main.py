"""Vercel entrypoint: exposes the FastAPI app at the service root.

If the platform mounts this service under a path prefix (e.g. /api/backend)
WITHOUT stripping it, set BASE_PATH=/api/backend in the service env and this
shim strips it so the app's /api/v1 routes resolve normally.
"""
import os

from app.main import app as fastapi_app

BASE_PATH = os.environ.get("BASE_PATH", "").rstrip("/")

if BASE_PATH:
    class _StripBasePath:
        def __init__(self, asgi_app):
            self.asgi_app = asgi_app

        async def __call__(self, scope, receive, send):
            if scope["type"] == "http" and scope.get("path", "").startswith(BASE_PATH):
                scope = dict(scope)
                scope["path"] = scope["path"][len(BASE_PATH):] or "/"
            await self.asgi_app(scope, receive, send)

    app = _StripBasePath(fastapi_app)
else:
    app = fastapi_app
