from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Form, Request

from app import auth, schema, util
from app.core.limiter import (
    AUTH_LIMIT,
    PASSWORD_RESET_LIMIT,
    PUBLIC_LIMIT,
    limiter,
)
from app.db.session import _db
from app.services.auth_service import AuthService

router = APIRouter(tags=["login"])


@router.get("/popDB/")
@limiter.limit(PUBLIC_LIMIT)
async def populate_db(request: Request, session: _db):
    """Endpoint para popular o banco (Usado para dev)"""
    from app.db.init_db import pop_db

    await pop_db(session)
    return "Ok"


@router.post("/login/access-token", response_model=schema.LoginResponse)
@limiter.limit(AUTH_LIMIT)
async def post_login(
    request: Request,
    login: Annotated[schema.Login, Form()],
    session: _db,
):
    """Logar"""

    user, sub = await AuthService.login(
        login.username, login.password, session
    )

    token = auth.encode_token(sub)
    response = schema.LoginResponse(
        access_token=token, token_type="Bearer", user=user
    )
    return response


@router.post(
    "/forgot-my-password/", response_model=schema.ForgotPasswordResponse
)
@limiter.limit(PASSWORD_RESET_LIMIT)
async def forgot_my_password(
    request: Request,
    email: schema.ForgotPassword,
    background_tasks: BackgroundTasks,
    session: _db,
):
    """Esqueci minha senha"""
    message, email_payload = await AuthService.request_password_reset(
        email.email, session
    )
    if email_payload:
        to, subject, body = email_payload
        background_tasks.add_task(util.send_email, to, subject, body)

    return schema.ForgotPasswordResponse(message=message)


@router.put("/new-password/")
@limiter.limit(PASSWORD_RESET_LIMIT)
async def put_password(
    request: Request,
    data: schema.ResetPassword,
    session: _db,
):
    """Altera a senha do usuario"""
    return await AuthService.reset_password(data, session)
