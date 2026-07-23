import hashlib
import uuid
from datetime import date, datetime

DATE_FORMAT = "%Y-%m-%d"


def generate_custom_uuid(custom_info: list[str]) -> str:
    combined_string = "".join(custom_info)
    hash_object = hashlib.sha256(combined_string.encode())
    hash_digest = hash_object.hexdigest()
    return str(uuid.UUID(hash_digest[:32]))


def date_to_str(value: datetime | date) -> str:
    return value.strftime(DATE_FORMAT)


def get_tenant_logger_header(obj) -> str:
    tenant = getattr(obj, "seller", None) or getattr(obj, "tenant", None)
    if tenant and getattr(tenant, "id", None):
        name = getattr(tenant, "name", "")
        return f"({tenant.id}) {name}:"
    return ""
