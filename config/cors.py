import os


def _allowed_origins():
    configured = os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "http://127.0.0.1:5173,http://localhost:5173",
    )
    return {origin.strip() for origin in configured.split(",") if origin.strip()}


class SimpleCORSMiddleware:
    """
    Minimal CORS support for local frontend/backend split.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.allowed_origins = _allowed_origins()

    def __call__(self, request):
        if request.method == "OPTIONS":
            response = self._build_preflight_response()
        else:
            response = self.get_response(request)

        origin = request.headers.get("Origin")
        if origin and origin in self.allowed_origins:
            response["Access-Control-Allow-Origin"] = origin
            response["Vary"] = "Origin"
            response["Access-Control-Allow-Credentials"] = "true"

        return response

    @staticmethod
    def _build_preflight_response():
        from django.http import HttpResponse

        response = HttpResponse(status=204)
        response["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response["Access-Control-Max-Age"] = "86400"
        return response
