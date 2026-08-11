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
    validate_permission_name,
)

__all__ = [
    "Cnpj",
    "Cpf",
    "CpfCnpj",
    "Email",
    "FullName",
    "Password",
    "PermissionName",
    "Username",
]

Password = Annotated[bytes, AfterValidator(normalize_password)]
FullName = Annotated[str, AfterValidator(normalize_capitalize)]
Username = Annotated[str, AfterValidator(normalize_lower)]
Email = Annotated[str, BeforeValidator(normalize_email)]
Cpf = Annotated[str, AfterValidator(validate_cpf)]
Cnpj = Annotated[str, AfterValidator(validate_cnpj)]
CpfCnpj = Annotated[str, AfterValidator(validate_cnpj_cpf)]
PermissionName = Annotated[str, AfterValidator(validate_permission_name)]
