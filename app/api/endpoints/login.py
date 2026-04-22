import json
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Header, Request
from fastapi.security import OAuth2PasswordRequestForm

from app import auth, core, error, models, schema, util
from app.core.limiter import limiter
from app.db.session import _db

router = APIRouter(tags=["login"])


@router.get("/popDB/")
def populate_db(session: _db):
    from app.db.init_db import pop_db

    pop_db(session)
    return "Ok"


@router.post("/login/access-token", response_model=schema.LoginResponse)
@limiter.limit("5/minute")
def post_login(
    request: Request,
    login: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: _db,
):
    """Logar"""
    try:
        user = models.Users.login(
            "email", login.username, login.password, session
        )
        key = [key.role.access_level for key in user.user_roles]
        sub = {
            "user_id": str(user.id),
            "key": [i for i in range(1, 10 + 1)] if 10 in key else key,
        }
        token = auth.encode_token(
            json.dumps(sub),
            core.settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        )
        response = schema.LoginResponse(
            access_token=token, token_type="Bearer", user=user
        )
        return response
    except Exception as e:
        raise error.custom_HTTPException(e)


@router.post(
    "/forgot-my-password/", response_model=schema.ForgotPasswordResponse
)
@limiter.limit("3/minute")
async def forgot_my_password(
    request: Request,
    email: schema.ForgotPassword,
    background_tasks: BackgroundTasks,
    session: _db,
):
    """Esqueci minha senha"""
    try:
        user = models.Users.get(session, "email", email.email)
        if not user:
            return schema.ForgotPasswordResponse(
                message="Se o e-mail estiver cadastrado, as instruções serão enviadas."
            )

        code = util.generate_code()

        # Envio sendo feito em background para não travar a UI/API
        background_tasks.add_task(
            util.send_email,
            email.email,
            core.settings.PROJECT_NAME,
            util.template_string(
                "reset_password.html",
                {
                    "code": code,
                },
            ),
        )
        hash_to_string = core.get_password_hash(code)

        from datetime import datetime, timedelta

        expiration = datetime.now() + timedelta(
            minutes=core.settings.RESET_PASSWORD_TOKEN_EXPIRATION_MINUTES
        )

        models.Users.update(
            user.id,
            session,
            reset_password_code=hash_to_string,
            reset_password_expiration=expiration,
        )

        return schema.ForgotPasswordResponse(
            message="Se o e-mail estiver cadastrado, as instruções serão enviadas."
        )
    except Exception as e:
        raise error.custom_HTTPException(e)


@router.put("/new-password/")
def put_password(
    data: schema.ResetPassword,
    session: _db,
):
    """Altera a senha do usuario"""
    try:
        data.code = util.normalize_uper(data.code)
        user = models.Users.get(session, "email", data.email)

        if (
            not user
            or not user.reset_password_code
            or not user.reset_password_expiration
        ):
            raise error.CustomException(401, "Email ou código inválido")

        from datetime import datetime

        if datetime.now() > user.reset_password_expiration:
            raise error.CustomException(401, "Código expirado")

        if not core.verify_password(data.code, user.reset_password_code):
            raise error.CustomException(401, "Email ou código inválido")

        # O schema Password (types_annotated) já realiza o hash internamente. Garantimos apenas o encode pra bytes (LargeBinary)
        senha_final = (
            data.password.encode("utf-8")
            if isinstance(data.password, str)
            else data.password
        )

        models.Users.update(
            user.id,
            session,
            password=senha_final,
            reset_password_code=None,
            reset_password_expiration=None,
        )
        return "Senha alterada"
    except Exception as e:
        raise error.custom_HTTPException(e)
