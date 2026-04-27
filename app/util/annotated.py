import json
from typing import Annotated

from fastapi import Depends, HTTPException, Query


class QueryParameters:
    """
    Classe para definir os parâmetros de consulta para endpoints.

    Args:
        all_data (bool, optional): Indica se todas as correspondências devem ser retornadas (True)
            ou apenas a primeira correspondência (False). Default é None.
        attribute (str, optional): Nome do atributo a ser buscado. Necessário quando "value" é utilizado.
        value (str, optional): Valor do atributo a ser buscado. Necessário quando "attribute" é utilizado.
            Para especificar um intervalo, utilize "|" , onde a primeira posição representa o limite inferior
            e a segunda posição representa o limite superior do intervalo. Exemplo: "10|20" para valores entre 10 e 20.
        operator (str, optional): Operador de comparação. Utilize "=" para igualdade, "~" para busca parcial (like),
            "!" para diferente, "<" para menor que, ">" para maior que, "<=" para menor ou igual a,
            ">=" para maior ou igual a, "|" para intervalo (por exemplo, "10|20" para valores entre 10 e 20). Default é "=".
        skip (int, optional): Número de itens a serem ignorados antes de começar a retornar os resultados.
            Default é 0. Se 'skip' e 'limit' forem fornecidos, o 'skip' atuará como um offset para a paginação,
            calculando a posição inicial dos itens a serem retornados.
        limit (int, optional): Número máximo de itens a serem retornados.
            Default é 100. Por exemplo, se limit=10, apenas os primeiros 10 resultados serão retornados.
        include (list[str], optional): Lista de atributos a serem devolvidos na consulta obs se None todos serão devolvidos.
    """

    def __init__(
        self,
        all_data: bool
        | None = Query(
            True,
            alias="all",
            description="Indica se todas as correspondências devem ser retornadas (True) "
            "ou apenas a primeira correspondência (False).",
        ),
        attribute: str
        | None = Query(
            None,
            description='Nome do atributo a ser buscado. Necessário quando "value" é utilizado.',
        ),
        value: str
        | None = Query(
            None,
            description='Valor do atributo a ser buscado. Necessário quando "attribute" é utilizado. '
            'Para especificar um intervalo, utilize "|" , onde a primeira posição '
            "representa o limite inferior e a segunda posição representa o limite superior do intervalo. "
            'Exemplo: "10|20" para valores entre 10 e 20.',
        ),
        json_string: str
        | None = Query(
            None,
            description="Estrutura JSON com um ou mais atributos para serem pesquisados, "
            "respeitando os parâmetros de igualdade ou busca parcial.",
        ),
        operator: str = Query(
            "=",
            description="""Operador de comparação. Utilize "=" para igualdade, "~" para busca parcial (like),
                "!" para diferente, "<" para menor que, ">" para maior que, "<=" para menor ou igual a,
                ">=" para maior ou igual a, "|" para intervalo.
                \n\n**Observação:** O intervalo deve estar no formato adequado ao tipo de dado da coluna.
                Por exemplo, para inteiros, use "10|20", para floats use "1.5|3.0",
                para datas use "2023-01-01|2024-01-01" e para horários use "08:00:00|12:00:00".""",
        ),
        skip: int
        | None = Query(
            0,
            description="Se 'skip' e 'limit' forem fornecidos, o 'skip' atuará como um offset para a paginação, "
            "calculando a posição inicial dos itens a serem retornados.",
        ),
        limit: int
        | None = Query(
            100,
            description="Número máximo de itens a serem retornados. "
            "Por exemplo, se limit=10, apenas os primeiros 10 resultados serão retornados. ",
        ),
        include: str
        | None = Query(
            None,
            description="Lista de atributos a serem excluídos da consulta.",
        ),
    ):
        valid_operators = {"=", "~", "!", "<", ">", "<=", ">=", "|"}

        if operator not in valid_operators:
            raise HTTPException(
                status_code=422,
                detail=f"Operador '{operator}' inválido. Os operadores válidos são: {', '.join(valid_operators)}",
            )

        if operator == "|" and (value is None or "|" not in value):
            raise HTTPException(
                status_code=422,
                detail="Quando o operador '|' é utilizado, o valor deve ser uma string representando o intervalo "
                "com os limites delimitados por '|'.",
            )

        if (attribute is None and value is not None) or (
            attribute is not None and value is None
        ):
            raise HTTPException(
                status_code=422,
                detail="Se um valor for fornecido, o atributo correspondente também deve ser fornecido, e vice-versa.",
            )

        if all_data is None:
            all_data = True

        if not all_data and (not attribute or not value):
            raise HTTPException(
                status_code=422,
                detail="Quando 'all' é False, 'attribute' e 'value' são obrigatórios!",
            )

        if (skip is not None and limit is None) or (
            limit is not None and skip is None
        ):
            raise HTTPException(
                status_code=422,
                detail="Se 'skip' ou 'limit' for fornecido, ambos devem ser fornecidos!",
            )

        self.all_data = all_data
        self.attribute = attribute
        self.value = value
        self.operator = operator
        self.skip = skip
        self.limit = limit

        if json_string is not None:
            try:
                self.json_string = json.loads(json_string)
                if not isinstance(self.json_string, dict):
                    raise HTTPException(
                        status_code=422,
                        detail="O parâmetro 'json_string' deve ser uma string JSON válida representando um dicionário!",
                    )
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=422,
                    detail="O parâmetro 'json_string' deve ser uma string JSON válida!",
                )
        else:
            self.json_string = None

        if include is not None:
            try:
                self.include = json.loads(include)
                if not isinstance(self.include, list):
                    raise HTTPException(
                        status_code=422,
                        detail="O parâmetro 'include' deve ser uma string JSON válida representando uma lista!",
                    )
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=422,
                    detail="O parâmetro 'include' deve ser uma list string JSON válida!",
                )
        else:
            self.include = None


QueryParametersDep = Annotated[dict, Depends(QueryParameters)]
