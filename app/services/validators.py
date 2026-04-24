def require_text(value: object, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field_name} 不能为空")
    return text


def optional_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def ensure_in(value: str, allowed: set[str], error_message: str) -> str:
    if value not in allowed:
        raise ValueError(error_message)
    return value
