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
from pydantic.types import UUID4

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
    filename = await save_file(file)
    return filename


@router.get("/{filename}", response_class=responses.FileResponse)
@limiter.limit(UPLOAD_LIMIT)
def get_file_by_filename(
    request: Request,
    filename: UUID4,
    Authentication: dict = Depends(
        auth.require_roles("User", "Manager", "Admin")
    ),
):
    if os.path.exists(f"{settings.UPLOAD_DIR}{filename!s}"):
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
            f"{settings.UPLOAD_DIR}{filename!s}", mime=True
        ),
    )
