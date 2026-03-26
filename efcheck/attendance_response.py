def is_attendance_response(url: str, method: str) -> bool:
    from urllib.parse import urlparse

    path = urlparse(url).path.rstrip("/")
    return path == "/web/v1/game/endfield/attendance" and method.upper() == "GET"
