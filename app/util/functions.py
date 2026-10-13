import csv
import logging
import os
import pathlib
import random
import re
import string
import uuid
from enum import Enum

import anyio
import magic
from fastapi import UploadFile

from app import error
from app.core.config import settings

logger = logging.getLogger(__name__)


__all__ = [
    "FileType",
    "camel_to_kebab",
    "camel_to_snake_case",
    "delete_file",
    "generate_code",
    "generate_cpf",
    "list_files",
    "pascal_to_camel_case",
    "pascal_to_kebab_case",
    "pascal_to_snake_case",
    "save_csv_file",
    "save_file",
    "snake_to_pascal_case",
    "validate_file_metadata",
]
CHUNK_SIZE = 1024 * 1024  # 1MB


class FileType(str, Enum):
    Application = "application"
    Image = "image"
    Text = "text"
    Video = "video"


ALLOWED_MIME_TYPES: dict[FileType, set[str]] = {
    FileType.Image: {"image/jpeg", "image/png", "image/webp"},
    FileType.Video: {"video/mp4", "video/webm", "video/quicktime"},
    FileType.Application: {"application/pdf", "text/plain"},
    FileType.Text: {"text/plain", "text/csv"},
}


def pascal_to_camel_case(string):
    return string[0].lower() + string[1:]


def pascal_to_snake_case(string):
    snake = ""
    for char in string:
        if char.isupper():
            snake += "_" + char.lower()
        else:
            snake += char
    return snake.lstrip("_")


def snake_to_pascal_case(string):
    return re.sub(r"(?:^|_)([a-z])", lambda m: m.group(1).upper(), string)


def pascal_to_kebab_case(string):
    kebab = ""
    for char in string:
        if char.isupper():
            kebab += "-" + char.lower()
        else:
            kebab += char
    return kebab.lstrip("-")


def camel_to_kebab(camel_str):
    kebab_str = re.sub(r"(?<!^)(?=[A-Z])", "-", camel_str).lower()
    return kebab_str


def camel_to_snake_case(camel_str):
    kebab_str = re.sub(r"(?<!^)(?=[A-Z])", "_", camel_str).lower()
    return kebab_str


def _safe_remove(path: str) -> None:
    """Remove um arquivo se ele existir, sem lançar erro caso contrario."""
    pathlib.Path(path).unlink(missing_ok=True)


async def validate_file_metadata(
    file: UploadFile, type_data: FileType
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

    allowed = ALLOWED_MIME_TYPES.get(type_data, set())

    # Lê os primeiros bytes para conferir os "magic bytes" reais do arquivo
    header = await file.read(2048)

    # IMPORTANTE: Reposiciona o ponteiro no início do arquivo para leituras futuras
    await file.seek(0)

    mime_type = str(magic.from_buffer(header, mime=True))

    if mime_type not in allowed:
        return f"Formato de mídia inválido ('{mime_type}'). Permitidos: {', '.join(allowed)}"

    return None


async def save_file(file: UploadFile, type_data: FileType) -> str:
    """Salva um UploadFile.

    Valida os metadados antes de iniciar a escrita e grava em modo streaming.

    Args:
        file (UploadFile): Arquivo enviado pelo usuário.
        type_data (FileType): Tipo esperado, usado para validar o mimetype real.

    Raises:
        CustomException: 422 se o mimetype for inválido.
        CustomException: 500 se ocorrer erro durante a escrita.

    Returns:
        str: Nome do arquivo salvo.
    """
    directory = settings.UPLOAD_DIR
    # 1. Valida antes de criar qualquer arquivo no sistema de arquivos
    err_msg = await validate_file_metadata(file, type_data)
    if err_msg:
        raise error.CustomException(422, err_msg)

    ext = pathlib.Path(file.filename).suffix if file.filename else ""
    name = f"{uuid.uuid4()}{ext}"
    final_path = os.path.join(directory, name)
    tmp_path = f"{final_path}.tmp"

    try:
        async with await anyio.open_file(tmp_path, "wb") as f:
            while chunk := await file.read(CHUNK_SIZE):
                await f.write(chunk)
    except Exception:
        logger.exception("Erro ao escrever arquivo temporário '%s'", tmp_path)
        await anyio.to_thread.run_sync(_safe_remove, tmp_path)
        raise error.CustomException(500, "Erro ao salvar o arquivo")

    await anyio.to_thread.run_sync(os.replace, tmp_path, final_path)
    return name


async def save_csv_file(directory: str, header: list, data: list) -> str:
    """Gera um arquivo CSV em `directory` (uso generico, fora do fluxo de categorias).

    Args:
        directory (str): Diretorio onde o CSV sera salvo.
        header (list): Lista com o cabecalho do CSV.
        data (list): Lista de linhas do CSV.

    Raises:
        CustomException: 404 se o diretorio nao existir.

    Returns:
        str: Nome do arquivo CSV gerado.
    """

    name = f"{uuid.uuid4()}.csv"
    filename = os.path.join(directory, name)

    def _write():
        try:
            with open(filename, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(header)
                writer.writerows(data)
        except FileNotFoundError:
            raise error.CustomException(
                404, "Arquivo ou diretorio nao encontrado"
            )

    await anyio.to_thread.run_sync(_write)
    return name


def delete_file(filename: str) -> bool:
    """Exclui um arquivo atraves de seu caminho e nome

    Args:
        filename (str): Nome do arquivo a ser excludio
    Raises:
        FileNotFoundError: Arquivo ou diretorio nao encontrado
    Returns:
        bool: retorna true em caso de sucesso
    """
    path = settings.UPLOAD_DIR
    try:
        os.remove(os.path.join(path, filename))
        return True
    except FileNotFoundError:
        raise error.CustomException(404, "Arquivo ou diretorio não encontrado")


def list_files(path: str) -> list:
    """Lista todos os arquivos de um diretorio

    Args:
        path (str): Diretorio para listar arquivos

    Returns:
        list: lista contendo nome de todos os arquivos de um diretorio
    """
    onlyfiles = [
        f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))
    ]
    return onlyfiles


def generate_cpf() -> str:
    """Gera um CPF valido

    Returns:
        str: retorna um CPF valido
    """
    cpf = [random.randint(0, 9) for x in range(9)]
    for _ in range(2):
        val = sum([(len(cpf) + 1 - i) * v for i, v in enumerate(cpf)]) % 11
        cpf.append(11 - val if val > 1 else 0)
    return "".join(str(digit) for digit in cpf)


def generate_code():
    """Código para verificação de email"""
    random_number = str(random.randint(1000, 9999))
    random_char = random.choice(string.ascii_uppercase) + random.choice(
        string.ascii_uppercase
    )
    return random_char + random_number
