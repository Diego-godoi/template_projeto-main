import pytest
from fastapi import HTTPException

from app.util.annotated import QueryParameters


def test_query_parameters_valid():
    qp = QueryParameters(
        all_data=True,
        attribute="name",
        value="test",
        operator="~",
        skip=5,
        limit=20,
        json_string='{"key": "value"}',
        include='["name"]',
    )
    assert qp.operator == "~"
    assert qp.skip == 5
    assert qp.limit == 20
    assert qp.json_string == {"key": "value"}
    assert qp.include == ["name"]


def test_query_parameters_invalid_operator():
    with pytest.raises(HTTPException) as exc_info:
        QueryParameters(operator="invalid", json_string=None, include=None)
    assert exc_info.value.status_code == 422
    assert "Operador" in exc_info.value.detail


def test_query_parameters_operator_interval_without_pipe():
    with pytest.raises(HTTPException) as exc_info:
        QueryParameters(
            attribute="age",
            value="10",
            operator="|",
            json_string=None,
            include=None,
        )
    assert exc_info.value.status_code == 422
    assert "limites delimitados por '|'" in exc_info.value.detail


def test_query_parameters_attribute_without_value():
    with pytest.raises(HTTPException) as exc_info:
        QueryParameters(
            attribute="age",
            value=None,
            operator="=",
            json_string=None,
            include=None,
        )
    assert exc_info.value.status_code == 422


def test_query_parameters_value_without_attribute():
    with pytest.raises(HTTPException) as exc_info:
        QueryParameters(
            attribute=None,
            value="test",
            operator="=",
            json_string=None,
            include=None,
        )
    assert exc_info.value.status_code == 422


def test_query_parameters_all_false_missing_attribute():
    with pytest.raises(HTTPException) as exc_info:
        QueryParameters(
            all_data=False,
            attribute=None,
            value=None,
            operator="=",
            json_string=None,
            include=None,
        )
    assert exc_info.value.status_code == 422
    assert "obrigatórios" in exc_info.value.detail


def test_query_parameters_skip_without_limit():
    with pytest.raises(HTTPException) as exc_info:
        QueryParameters(
            skip=10, limit=None, operator="=", json_string=None, include=None
        )
    assert exc_info.value.status_code == 422


def test_query_parameters_limit_without_skip():
    with pytest.raises(HTTPException) as exc_info:
        QueryParameters(
            skip=None, limit=10, operator="=", json_string=None, include=None
        )
    assert exc_info.value.status_code == 422


def test_query_parameters_invalid_json_string():
    with pytest.raises(HTTPException) as exc_info:
        QueryParameters(json_string="not a dict", operator="=", include=None)
    assert exc_info.value.status_code == 422


def test_query_parameters_invalid_include():
    with pytest.raises(HTTPException) as exc_info:
        QueryParameters(include="not a list", operator="=", json_string=None)
    assert exc_info.value.status_code == 422
