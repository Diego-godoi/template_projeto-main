from typing import Annotated

from pydantic.functional_validators import AfterValidator, BeforeValidator

from app.util.validators import (
    normalize_address_number,
    normalize_capitalize,
    normalize_cep,
    normalize_digits,
    normalize_email,
    normalize_lower,
    normalize_password,
    normalize_phone,
    normalize_trim,
    normalize_upper,
    validate_cnpj,
    validate_cnpj_cpf,
    validate_cpf,
)

__all__ = [
    "Cep",
    "Cnpj",
    "Cpf",
    "CpfCnpj",
    "Email",
    "FullName",
    "OptionalCep",
    "OptionalCpf",
    "OptionalEmail",
    "OptionalPhone",
    "OptionalStrippedStr",
    "Password",
    "StrippedStr",
    "UpperStr",
    "Username",
]

StrippedStr = Annotated[str, BeforeValidator(normalize_trim)]
OptionalStrippedStr = Annotated[str | None, BeforeValidator(normalize_trim)]
UpperStr = Annotated[str, BeforeValidator(normalize_upper)]
CapitalizeStr = Annotated[str, AfterValidator(normalize_capitalize)]
OptionalCapitalizeStr = Annotated[
    str | None, AfterValidator(normalize_capitalize)
]
AddressNumberStr = Annotated[
    str | None, BeforeValidator(normalize_address_number)
]
Password = Annotated[str, AfterValidator(normalize_password)]
FullName = Annotated[str, AfterValidator(normalize_capitalize)]
Username = Annotated[str, AfterValidator(normalize_lower)]
Email = Annotated[str, BeforeValidator(normalize_email)]
OptionalEmail = Annotated[str | None, BeforeValidator(normalize_email)]
Cpf = Annotated[
    str, BeforeValidator(normalize_digits), AfterValidator(validate_cpf)
]
OptionalCpf = Annotated[
    str | None,
    BeforeValidator(normalize_digits),
    AfterValidator(validate_cpf),
]
Cnpj = Annotated[
    str, BeforeValidator(normalize_digits), AfterValidator(validate_cnpj)
]
CpfCnpj = Annotated[
    str,
    BeforeValidator(normalize_digits),
    AfterValidator(validate_cnpj_cpf),
]
Phone = Annotated[str, BeforeValidator(normalize_phone)]
OptionalPhone = Annotated[str | None, BeforeValidator(normalize_phone)]
Cep = Annotated[str, BeforeValidator(normalize_cep)]
OptionalCep = Annotated[str | None, BeforeValidator(normalize_cep)]
