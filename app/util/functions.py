import csv
import os
import random
import re
import string
import uuid
from io import BytesIO

import magic
from fastapi import UploadFile

from app import error
from app.core.config import settings

__all__ = [
    "generate_cpf",
    "save_file",
    "delete_file",
    "save_csv_file",
    "list_files",
    "generate_code",
    "camel_to_kebab",
    "camel_to_snake_case",
    "pascal_to_camel_case",
    "pascal_to_snake_case",
    "pascal_to_kebab_case",
    "snake_to_pascal_case",
]


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


async def save_file(file: UploadFile, type: str) -> str:
    """Salva arquivos

    Args:
        path (str): Diretorio onde sera salvo o arquivo
        file (UploadFile): fastapi file upload
        type (str): tipo do file obs: 'video' , 'image' ...

    Raises:
        CustomException: 400 Arquivo ou diretorio não encontrado
        CustomException: 422 Formato de media invalido

    Returns:
        str: Retorna o nome do arquivo
    """

    path = settings.UPLOAD_DIR

    if not os.path.exists(path):
        raise error.CustomException(
            status_code=400,
            detail="Arquivo ou diretorio não encontrado",
        )
    w_file = BytesIO()
    conteudo = await file.read()
    w_file.write(conteudo)
    w_file.seek(0)
    if str(magic.from_buffer(w_file.read(), True)).split("/")[0] != type:
        raise error.CustomException(422, "Formato de media invalido")
    w_file.seek(0)
    name = str(uuid.uuid4())
    filename = os.path.join(path, name)
    with open(filename, "wb") as f:
        f.write(w_file.getbuffer())
    return name


def save_csv_file(path: str, header: list, data: list) -> str:
    name = str(uuid.uuid4())
    filename = f"{path}{name}"
    try:
        with open(filename, "w") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(data)
    except FileNotFoundError:
        raise error.CustomException(404, "Arquivo ou diretorio não encontrado")
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
