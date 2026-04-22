from pydantic import BaseModel

__all__ = ["MetaData"]


class MetaData(BaseModel):
    """
    Schema para metadados de paginação em listagens.

    Attributes:
        total_items (int): Quantidade total de registros encontrados no banco.
    """

    total_items: int
