from fastapi import APIRouter, HTTPException, Request, Response, status

from app.api.deps import CurrentUser, DbSession
from app.core.config import get_settings
from app.schemas.auth import AuthResponse, LoginRequest, UserResponse
from app.services.auth import (
    authenticate_user,
    create_user_session,
    delete_user_session,
    write_login_audit,
)
from app.services.login_rate_limit import login_rate_limiter

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, request: Request, response: Response, session: DbSession):
    rate_limit_key = request.client.host if request.client else "unknown"
    login_rate_limiter.check(rate_limit_key)
    user = authenticate_user(session, payload.username, payload.password)
    ip_address = request.client.host if request.client else None
    write_login_audit(session, user=user, success=user is not None, ip_address=ip_address)
    if user is None:
        session.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误"
        )

    login_rate_limiter.reset(rate_limit_key)
    raw_token = create_user_session(
        session, user, ip_address, request.headers.get("user-agent")
    )
    session.commit()
    settings = get_settings()
    response.set_cookie(
        key=settings.session_cookie_name,
        value=raw_token,
        max_age=settings.session_ttl_seconds,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        path="/",
    )
    return AuthResponse(user=UserResponse.model_validate(user))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request,
    response: Response,
    session: DbSession,
) -> None:
    session_token = request.cookies.get(get_settings().session_cookie_name)
    if session_token:
        delete_user_session(session, session_token)
        session.commit()
    response.delete_cookie(get_settings().session_cookie_name, path="/")


@router.get("/me", response_model=AuthResponse)
def me(current_user: CurrentUser) -> AuthResponse:
    return AuthResponse(user=UserResponse.model_validate(current_user))
