from ninja import Schema


class MessageEnvelope(Schema):
    success: bool
    message: str


class ErrorEnvelope(Schema):
    success: bool
    message: str
    error: str


def error_payload(message: str, code: str) -> dict:
    return {"success": False, "message": message, "error": code}
