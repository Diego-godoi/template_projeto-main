import csv
import logging
import os
import pathlib
import random
import re
import string
import uuid

import anyio
from fastapi import UploadFile

from app import error
from app.core.config import settings

logger = logging.getLogger(__name__)

__all__ = [
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
]
CHUNK_SIZE = 1024 * 1024  # 1MB


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
    if os.path.exists(path):
        os.remove(path)


async def save_file(file: UploadFile) -> str:
    """Salva um UploadFile na subpasta correspondente à sua categoria.

    Args:
        file (UploadFile): Arquivo enviado pelo usuário.

    Raises:
        CustomException: 500 se ocorrer erro durante a escrita.

    Returns:
        str: Nome do arquivo salvo.
    """

    directory = settings.UPLOAD_DIR
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


def delete_file(path: str, filename: str) -> bool:
    """Exclui um arquivo atraves de seu caminho e nome

    Args:
        path (str): Diretorio onde encontra-se o arquivo
        filename (str): Nome do arquivo a ser excludio
    Raises:
        FileNotFoundError: Arquivo ou diretorio nao encontrado
    Returns:
        bool: retorna true em caso de sucesso
    """
    try:
        os.remove(f"{path}{filename}")
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
