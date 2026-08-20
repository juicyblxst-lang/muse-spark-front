from fastapi import Request, Response

from app.auth import User, current_user

async def require_current_user(request: Request, response: Response) -> User:
    return await current_user(request, response)
