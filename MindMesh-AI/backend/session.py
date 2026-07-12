import uuid

from fastapi import Request


def get_current_user_id(request: Request) -> str:
    """Return the stable anonymous user ID stored in the signed session."""
    user_id = request.session.get("user_id")
    if not user_id:
        user_id = str(uuid.uuid4())
        request.session["user_id"] = user_id
    return user_id
