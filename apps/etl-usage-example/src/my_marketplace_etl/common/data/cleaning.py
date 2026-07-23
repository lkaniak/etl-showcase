from decimal import Decimal, InvalidOperation
import re


def empty_to_null(value):
    if value == "" or value is None:
        return None
    return value


def normalize_status(value: str | None) -> str | None:
    if value is None:
        return None
    return str(value).strip().lower()


def parse_amount(value) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float, Decimal)):
        return float(value)
    cleaned = str(value).replace(",", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


def normalize_source_medium(value: str | None) -> str | None:
    if value is None:
        return None
    value = str(value).strip().lower()
    value = re.sub(r"\s*/\s*", " / ", value)
    return value


def fill_null_int(value, default: int = 0) -> int:
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
