import http
from typing import Any

__all__ = [
    "CustomException",
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
