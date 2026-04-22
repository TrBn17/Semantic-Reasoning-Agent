from fastapi import Response


PUBLIC_ROUTE = {"x-api-audience": "public", "x-api-primary": True}
ADVANCED_ROUTE = {"x-api-audience": "advanced", "x-api-primary": False}
INTERNAL_ROUTE = {"x-api-audience": "internal/admin", "x-api-primary": False}


def mark_deprecated(
    response: Response,
    *,
    replacement: str,
    message: str | None = None,
) -> None:
    notice = message or f"Deprecated API. Use {replacement}."
    response.headers["Deprecation"] = "true"
    response.headers["Link"] = f'<{replacement}>; rel="successor-version"'
    response.headers["Warning"] = f'299 - "{notice}"'
