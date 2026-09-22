from typing import Annotated

from pydantic.functional_validators import AfterValidator, BeforeValidator

from app.util.validators import (
    normalize_capitalize,
    normalize_email,
    normalize_lower,
    normalize_password,
    validate_cnpj,
    validate_cnpj_cpf,
    validate_cpf,
)

from .enums import FileType

__all__ = [
    "Cnpj",
    "Cpf",
    "CpfCnpj",
    "Email",
    "FileType",
    "FullName",
    "Password",
    "Username",
]


Password = Annotated[str, AfterValidator(normalize_password)]
FullName = Annotated[str, AfterValidator(normalize_capitalize)]
Username = Annotated[str, AfterValidator(normalize_lower)]
Email = Annotated[str, BeforeValidator(normalize_email)]
Cpf = Annotated[str, AfterValidator(validate_cpf)]
Cnpj = Annotated[str, AfterValidator(validate_cnpj)]
CpfCnpj = Annotated[str, AfterValidator(validate_cnpj_cpf)]
