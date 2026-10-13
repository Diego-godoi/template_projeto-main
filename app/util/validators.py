import re
from itertools import cycle
from typing import TYPE_CHECKING

import magic
from email_validator import EmailNotValidError, validate_email
from fastapi import UploadFile

from app import error

if TYPE_CHECKING:
    from app.schema.enums import FileType

__all__ = [
    "normalize_address_number",
    "normalize_capitalize",
    "normalize_cep",
    "normalize_digits",
    "normalize_email",
    "normalize_lower",
    "normalize_password",
    "normalize_phone",
    "normalize_trim",
    "normalize_uper",
    "normalize_upper",
    "validate_cnpj",
    "validate_cnpj_cpf",
    "validate_cpf",
]

ALLOWED_MIME_TYPES: dict[str, set[str]] = {
    "image": {"image/jpeg", "image/png", "image/webp"},
    "video": {"video/mp4", "video/webm", "video/quicktime"},
    "application": {"application/pdf"},
    "text": {"text/plain", "text/csv"},
}


def normalize_trim(key: str | None) -> str | None:
    """Remove espaços externos e converte strings vazias em ``None``."""
    if key is None:
        return None
    value = str(key).strip()
    if value.lower() in {"none", "null"}:
        return None
    return value or None


def normalize_digits(key: str | None) -> str | None:
    """Remove máscaras de identificadores numéricos."""
    value = normalize_trim(key)
    if value is None:
        return None
    digits = re.sub(r"\D", "", value)
    if not digits:
        raise error.CustomException(
            422, "O campo deve conter ao menos um dígito numérico."
        )
    return digits


# validador de CPF
def validate_cpf(key: str) -> str | None:
    if key is None:
        return None
    value = str(key).strip()
    if not value:
        return None
    key = re.sub(r"\D", "", value)

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


def validate_cnpj(cnpj: str) -> str | None:
    """Valida o CNPJ de acordo com o cálculo dos dígitos verificadores."""
    if cnpj is None:
        return None
    value = str(cnpj).strip()
    if not value:
        return None
    cnpj = re.sub(r"\D", "", value)

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
    if key is None:
        return None
    value = str(key).strip()
    if not value:
        return None
    key = re.sub(r"\D", "", value)
    if len(key) == 11:
        return validate_cpf(key)
    if len(key) == 14:
        return validate_cnpj(key)
    else:
        raise error.CustomException(422, "Deve conter um CPF ou CNPJ valido")


# Aplica Primeria letra maiuscula em uma string
def normalize_capitalize(key: str):
    key = normalize_trim(key)
    if key is None:
        return None
    return " ".join(word.capitalize() for word in key.lower().split())


def normalize_uper(key: str):
    key = normalize_trim(key)
    if key is None:
        return None
    return " ".join(word.upper() for word in key.split())


def normalize_upper(key: str | None):
    """Normaliza texto para caixa alta, preservando apenas conteúdo útil."""
    return normalize_uper(key)


def normalize_password(key: bytes):
    """
    Nota: Hashing removido daqui para evitar conflito async e double-hash.
    A camada de Service agora é responsável pelo hashing assíncrono.
    """
    return key


def normalize_lower(key: str):
    key = normalize_trim(key)
    if key is None:
        return None
    return " ".join(word.lower() for word in key.split())


def normalize_phone(key: str):
    key = normalize_digits(key)
    if key is None:
        return None
    if len(key) > 13 or len(key) < 11:
        raise error.CustomException(
            status_code=422,
            detail="Formato de telefone invalido, deve conter no minimo 11 e no maximo 13 digitos",
        )
    return key


def normalize_email(key: str) -> str | None:
    key = normalize_trim(key)
    if key is None:
        return None
    try:
        valid = validate_email(key, check_deliverability=False)
        key = valid.normalized
    except EmailNotValidError:
        raise error.CustomException(
            status_code=422,
            detail="Formato de email invalido",
        )
    return key.lower()


async def validate_file_metadata(
    file: UploadFile, type_data: "FileType"
) -> str | None:
    """Valida o MIME type real de um arquivo sem consumi-lo da memória/disco.

    Lê apenas os primeiros bytes para detectar o tipo MIME real via magic bytes.
    Ao final, reposiciona o ponteiro de leitura no início (seek(0)) para que o
    arquivo possa ser lido/salvo posteriormente sem perdas.

    Args:
        file (UploadFile): Arquivo enviado pelo cliente.
        type_data (FileType): Tipo esperado (Image, Video, Application).

    Returns:
        str | None: Retorna a mensagem de erro se inválido, ou None se válido.
    """
    if not file or not file.filename:
        return "Arquivo não fornecido"

    allowed = ALLOWED_MIME_TYPES.get(type_data.value, set())

    # Lê os primeiros bytes para conferir os "magic bytes" reais do arquivo
    header = await file.read(2048)

    # IMPORTANTE: Reposiciona o ponteiro no início do arquivo para leituras futuras
    await file.seek(0)

    mime_type = str(magic.from_buffer(header, mime=True))

    if mime_type not in allowed:
        return f"Formato de mídia inválido ('{mime_type}'). Permitidos: {', '.join(allowed)}"

    return None


def normalize_cep(key: str) -> str:
    # Remove tudo que não for número (ex: "01310-100" vira "01310100")
    key = normalize_digits(key)
    if key is None:
        return None

    if len(key) != 8:
        raise error.CustomException(
            422,
            "CEP inválido. O campo deve conter exatamente 8 dígitos numéricos.",
        )

    # Evita CEPs falsos comuns com números repetidos
    if key == key[0] * 8:
        raise error.CustomException(422, "CEP inválido.")

    return key


def normalize_address_number(key: str | None) -> str | None:
    """
    Normaliza o número do endereço.
    Permite Null/None, mas se houver valor, deve ser exclusivamente numérico.
    """
    value = normalize_trim(key)

    # Permite ser nulo
    if value is None:
        return None

    # Verifica se a string contém APENAS números (sem letras ou caracteres especiais como '-' ou ',')
    if not value.isdigit():
        raise error.CustomException(
            422,
            "O número do endereço deve conter apenas números, sem letras ou caracteres especiais.",
        )

    return value
