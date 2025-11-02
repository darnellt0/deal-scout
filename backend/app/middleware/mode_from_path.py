from starlette.middleware.base import BaseHTTPMiddleware


class PathModeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        path = request.url.path or ""
        if path.startswith("/buyer/"):
            request.state.user_mode = "buyer"
        elif path.startswith("/seller/"):
            request.state.user_mode = "seller"
        else:
            request.state.user_mode = None
        return await call_next(request)
