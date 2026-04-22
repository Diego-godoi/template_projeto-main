from fastapi import Form
from pydantic import BaseModel, Field, model_validator

from app import error

from .types_annotated import Email, Password
from .users_schema import GetUsers

__all__ = [
    "Login",
    "LoginResponse",
    "ForgotPassword",
    "ForgotPasswordResponse",
    "ResetPassword",
]


class Login(BaseModel):
    """
    Schema para autenticação de usuários no sistema.

    Attributes:
        username (str): E-mail do usuário usado para login.
        password (str): Senha do usuário.
    """

    username: str = Field(..., description="E-mail de acesso do usuário")
    password: str = Field(..., description="Senha secreta do usuário")

    @classmethod
    def as_form(
        cls,
        username: Email = Form(..., description="email Documentar"),
        password: str = Form(..., description="password Documentar"),
    ):
        return cls(
            username=username,
            password=password,
        )

    @model_validator(mode="before")
    @classmethod
    def validators_user(self, data):
        try:
            data["username"] = data["username"].lower()

            return data
        except Exception as e:
            raise error.custom_HTTPException(e)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: GetUsers

    class Config:
        from_attributes = True


class ForgotPassword(BaseModel):
    """
    Schema para solicitação de recuperação de senha.

    Attributes:
        email (Email): E-mail da conta que deseja recuperar.
    """

    email: Email = Field(..., description="E-mail da conta para recuperação")


class ForgotPasswordResponse(BaseModel):
    message: str

    class Config:
        from_attributes = True


class ResetPassword(BaseModel):
    """
    Schema para redefinição de senha após o recebimento do código.

    Attributes:
        email (Email): E-mail da conta.
        code (str): Código recebido por e-mail.
        password (Password): Nova senha a ser definida.
    """

    email: Email = Field(..., description="E-mail da conta")
    code: str = Field(..., description="Código de recuperação recebido")
    password: Password = Field(
        description="Nova senha (mínimo 6 caracteres)", min_length=6
    )
