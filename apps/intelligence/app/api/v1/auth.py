from fastapi import APIRouter, Request, Response

from app.auth import AuthRequest, Session, SignUpRequest, User, current_user, sign_in, sign_out, sign_up

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/sign-in", response_model=Session)
async def auth_sign_in(payload: AuthRequest, response: Response) -> Session:
    return await sign_in(payload, response)

@router.post("/sign-up", response_model=Session)
async def auth_sign_up(payload: SignUpRequest, response: Response) -> Session:
    return await sign_up(payload, response)

@router.post("/sign-out", status_code=204)
async def auth_sign_out(request: Request, response: Response) -> Response:
    await sign_out(request, response)
    return response

@router.get("/me", response_model=User)
async def auth_me(request: Request, response: Response) -> User:
    return await current_user(request, response)
