import re
from itertools import cycle

from email_validator import validate_email

from app import error

__all__ = [
    "normalize_capitalize",
    "normalize_email",
    "normalize_lower",
    "normalize_password",
    "normalize_phone",
    "normalize_uper",
    "validate_cnpj",
    "validate_cnpj_cpf",
    "validate_cpf",
    "validate_permission_name",
]


# validador de CPF
def validate_cpf(key: str) -> str:
    # Remover espaços em branco e caracteres não numéricos
    key = re.sub(r"\D", "", key.strip())

    # Verificar comprimento e se todos os caracteres são dígitos
    if len(key) != 11 or not key.isdigit():
        raise error.CustomException(
            422,
            "CPF inválido. O campo deve conter exatamente 11 dígitos numéricos.",
        )

    # Verificar se o CPF é uma sequência repetida
    if key in (c * 11 for c in "1234567890"):
        raise error.CustomException(422, "CPF inválido")

    # Calculando os dígitos verificadores
    def calcular_digito(digitos, pesos):
        soma = sum(int(d) * p for d, p in zip(digitos, pesos))
        resto = soma % 11
        return 0 if resto < 2 else 11 - resto

    pesos_primeiro_dv = list(range(10, 1, -1))
    pesos_segundo_dv = list(range(11, 1, -1))

    primeiro_dv = calcular_digito(key[:-2], pesos_primeiro_dv)
    segundo_dv = calcular_digito(key[:-1] + str(primeiro_dv), pesos_segundo_dv)

    if primeiro_dv != int(key[-2]) or segundo_dv != int(key[-1]):
        raise error.CustomException(422, "CPF inválido")

    return key


def validate_cnpj(cnpj: str) -> str:
    """Valida o CNPJ de acordo com o cálculo dos dígitos verificadores."""

    # Remove qualquer caractere que não seja dígito
    cnpj = "".join(filter(str.isdigit, cnpj))

    if len(cnpj) != 14:
        raise error.CustomException(
            422,
            "CNPJ inválido. O campo deve conter exatamente 14 dígitos numéricos",
        )

    # Verifica se o CNPJ tem todos os dígitos iguais (caso inválido)
    if cnpj in (c * 14 for c in "1234567890"):
        raise error.CustomException(
            422, "CNPJ inválido. CNPJ não pode ter todos os dígitos iguais."
        )

    # Função auxiliar para calcular os dígitos verificadores
    def calculate_digit(cnpj_base: str) -> int:
        """Calcula o dígito verificador para o CNPJ base."""
        weights = cycle(range(2, 10))
        soma = sum(int(num) * next(weights) for num in reversed(cnpj_base))
        remainder = soma % 11
        return 0 if remainder < 2 else 11 - remainder

    # Primeiro dígito verificador
    cnpj_base = cnpj[:12]
    dv1 = calculate_digit(cnpj_base)

    # Segundo dígito verificador
    cnpj_base = cnpj[:12] + str(dv1)
    dv2 = calculate_digit(cnpj_base)

    # Verifica se os dígitos verificadores calculados correspondem ao CNPJ
    if cnpj[-2:] != f"{dv1}{dv2}":
        raise error.CustomException(
            422, "CNPJ inválido. Dígito verificador incorreto."
        )

    # Retorna o CNPJ caso seja válido
    return cnpj


# Valida um dado que pode ser CPF OU CNPJ
def validate_cnpj_cpf(key: str):
    if not key:
        return key
    if len(key) == 11:
        return validate_cpf(key)
    if len(key) == 14:
        return validate_cnpj(key)
    else:
        raise error.CustomException(422, "Deve conter um CPF ou CNPJ valido")


# Aplica Primeria letra maiuscula em uma string
def normalize_capitalize(key: str):
    if not key:
        return key
    key = key.lower()
    return " ".join((word.capitalize()) for word in key.split(" "))


def normalize_uper(key: str):
    if not key:
        return key
    return " ".join((word.upper()) for word in key.split(" "))


def normalize_password(key: bytes):
    """
    Nota: Hashing removido daqui para evitar conflito async e double-hash.
    A camada de Service agora é responsável pelo hashing assíncrono.
    """
    return key


def normalize_lower(key: str):
    if not key:
        return key
    return " ".join((word.lower()) for word in key.split(" "))


def normalize_phone(key: str):
    if not key:
        return key
    key = re.sub("[^0-9]+", "", key)
    if len(key) > 13 or len(key) < 11:
        raise error.CustomException(
            status_code=422,
            detail="Formato de telefone invalido, deve conter no minimo 11 e no maximo 13 digitos",
        )
    return key


def normalize_email(key: str) -> str:
    if not key:
        return key
    try:
        valid = validate_email(key, check_deliverability=False)
        key = valid.normalized
    except Exception:  # noqa: BLE001 — barreira final, não deve vazar detalhe interno
        raise error.CustomException(
            status_code=422,
            detail="Formato de email invalido",
        )
    return key.lower()


def validate_permission_name(v: str) -> str:
    """Valida que o nome da permissão segue o formato 'verbo:modulo'.

    Ex: 'read:users', 'write:role-permissions'.
    """
    if not v:
        return v

    v = v.strip().lower()
    pattern = r"^[a-z0-9_-]+:[a-z0-9_-]+$"

    if not re.match(pattern, v):
        raise ValueError(
            "O nome da permissão deve estar no formato 'verbo:modulo' "
            "(ex: 'read:users' ou 'write:role-permissions')"
        )

    return v
