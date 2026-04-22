import http
import logging
from typing import Any, NoReturn

from fastapi import HTTPException

__all__ = [
    "CustomException",
    "custom_HTTPException",
    "DatabaseException",
    "ValidationException",
]


class ConstructException(Exception):
    """
    Classe base de exceção para construir exceções personalizadas com um código de status
    e uma mensagem de detalhe opcional.

    Atributos:
        status_code (int): O código de status HTTP associado a esta exceção.
        detail (Any): A mensagem de detalhe opcional associada a esta exceção.
    """

    def __init__(
        self,
        status_code: int,
        detail: Any = None,
    ) -> None:
        if detail is None:
            detail = http.HTTPStatus(status_code).phrase
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


# Alias público mantido para compatibilidade com todos os imports existentes
CustomException = ConstructException


class DatabaseException(ConstructException):
    """
    Exceção pura de Banco de Dados. Lançada pela camada ORM (base_class.py).
    Não deve ser vazada diretamente ao usuário sem um Exception Handler.
    """

    def __init__(
        self,
        detail: str = "Erro interno de Banco de Dados",
        status_code: int = 400,
    ):
        super().__init__(status_code=status_code, detail=detail)


class ValidationException(ConstructException):
    """
    Exceção de validação que acumula múltiplos erros de negócio.

    Cada erro deve ser um dict no formato:
        {"loc": ["body", "campo"], "msg": "mensagem", "type": "value_error"}

    Uso:
        errors = []
        errors.append({"loc": ["body", "email"], "msg": "Email já cadastrado.", "type": "value_error"})
        if errors:
            raise ValidationException(errors)
    """

    def __init__(self, errors: list[dict]) -> None:
        super().__init__(status_code=422, detail=errors)


def custom_HTTPException(e: Any) -> NoReturn:
    """
    Função para manipular exceções personalizadas e lançar uma HTTPException
    com um código de status e uma mensagem de detalhe adequados.

    Exceções sem `status_code` (inesperadas) são logadas como ERROR antes de
    serem convertidas em HTTP 500, evitando vazar detalhes internos ao cliente.

    Args:
        e (Any): A exceção a ser manipulada.

    Raises:
        HTTPException: Sempre levantada — nunca retorna.
    """
    if not hasattr(e, "status_code"):
        logging.error(
            "Exceção inesperada capturada [%s]: %s",
            type(e).__name__,
            str(e),
        )
    raise HTTPException(
        status_code=e.status_code if hasattr(e, "status_code") else 500,
        detail=e.detail
        if hasattr(e, "status_code")
        else "Erro Interno da API",
    )
