import os
from typing import Annotated

import magic
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Request,
    UploadFile,
    responses,
)

from app import auth, error
from app.core.config import settings
from app.core.limiter import UPLOAD_LIMIT, limiter
from app.schema import FileType
from app.util.functions import save_file
from app.util.validators import validate_file_metadata

router = APIRouter(prefix="/file", tags=["File"])


@router.post("/")
@limiter.limit(UPLOAD_LIMIT)
async def create_file(
    request: Request,
    file: Annotated[UploadFile, File(...)],
    type_data: Annotated[FileType, Form(...)],
    Authentication: dict = Depends(
        auth.require_roles("User", "Manager", "Admin")
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
    err_msg = await validate_file_metadata(file, type_data)
    if err_msg:
        raise error.CustomException(422, err_msg)
    filename = await save_file(file, type_data)
    return filename


@router.get("/{filename}")
@limiter.limit(UPLOAD_LIMIT)
async def get_file_by_filename(
    request: Request,
    filename: str,
):
    """Busca um arquivo salvo pelo nome e pela sua categoria."""
    file_path = os.path.join(settings.UPLOAD_DIR, filename)

    if not os.path.exists(file_path):
        raise error.CustomException(
            status_code=404, detail="Arquivo não encontrado"
        )

    # Detecta o tipo do arquivo (video/mp4, image/png, etc)
    mime_type = magic.from_file(file_path, mime=True)

    return responses.FileResponse(
        path=file_path,
        media_type=mime_type,
        headers={"Content-Disposition": "inline"},
    )
