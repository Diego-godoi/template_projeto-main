import os
from enum import Enum

import magic
from fastapi import APIRouter, File, Form, Security, UploadFile, responses
from pydantic.types import UUID4

from app import auth, error
from app.core.config import settings
from app.util.functions import save_file

router = APIRouter(prefix="/file", tags=["File"])


class FileType(str, Enum):
    Application = "application"
    Image = "image"
    Text = "text"
    Video = "video"


@router.post("/")
def create_file(
    file: UploadFile = File(...),
    type_data: FileType = Form(...),
    Authentication: dict = Security(
        auth.get_current_payload, scopes=["user", "admin"]
    ),
) -> str:
    """
    Cria um novo arquivo.

    Args:
        file (UploadFile): O arquivo a ser enviado.
        type_data (FileType): O tipo de arquivo a ser salvo.

    Returns:
        str: O nome do arquivo salvo.

    Raises:
        HTTPException: Se ocorrer um erro durante o processo de criação do arquivo.

    Esta função cria um novo arquivo com base nos parâmetros fornecidos.
    Ele salva o arquivo na pasta de upload especificada no diretório de configuração.
    O nome do arquivo salvo é retornado como uma string.

    Notas de Implementação:
    - A função `util.save_file` é usada para salvar o arquivo.
    - O diretório de upload é configurado no arquivo de configuração `core.settings.UPLOAD_DIR`.
    - Os tipos de arquivo suportados são definidos pelo enumerador `core.models.FileType`.

    """

    filename = save_file(file, type_data)
    return filename


@router.get("/{filename}", response_class=responses.FileResponse)
def get_file_by_filename(
    filename: UUID4,
    Authentication: dict = Security(
        auth.get_current_payload, scopes=["user", "admin"]
    ),
):
    if os.path.exists(f"{settings.UPLOAD_DIR}{str(filename)}"):
        image = os.path.join(settings.UPLOAD_DIR, str(filename))

        def iterfile():
            with open(image, mode="rb") as file_like:
                yield from file_like

    else:
        raise error.CustomException(
            status_code=404, detail="Imagem nao encontrada"
        )
    return responses.StreamingResponse(
        iterfile(),
        media_type=magic.from_file(
            f"{settings.UPLOAD_DIR}{str(filename)}", mime=True
        ),
    )
