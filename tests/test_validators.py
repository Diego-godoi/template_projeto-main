# tests/test_validators.py
"""
Testes puros das funções utilitárias de validação (Fase 1).
"""

import pytest

from app.error import CustomException
from app.util import validators
from app.util.functions import generate_cpf

# ==========================================
# Testes de Normalização (Strings)
# ==========================================


def test_normalize_capitalize():
    assert validators.normalize_capitalize("joAO silVa") == "Joao Silva"
    assert validators.normalize_capitalize("maria") == "Maria"
    assert validators.normalize_capitalize("") == ""
    assert validators.normalize_capitalize(None) is None


def test_normalize_uper():
    assert validators.normalize_uper("joao silva") == "JOAO SILVA"
    assert validators.normalize_uper("") == ""
    assert validators.normalize_uper(None) is None


def test_normalize_lower():
    assert validators.normalize_lower("JOao SIlva") == "joao silva"
    assert validators.normalize_lower("") == ""
    assert validators.normalize_lower(None) is None


# ==========================================
# Testes de Normalização (Senha)
# ==========================================


def test_normalize_password():
    # Retorna o hash bcrypt
    hashed = validators.normalize_password(b"senha123")
    assert hashed != b"senha123"
    assert len(hashed) > 10

    assert validators.normalize_password(None) is None
    assert validators.normalize_password(b"") == b""


# ==========================================
# Testes de CPF e CNPJ
# ==========================================


def test_validate_cpf_valido():
    cpf_valido = generate_cpf()
    # Verifica se passa silenciosamente retornando a string original ou limpa
    resultado = validators.validate_cpf(cpf_valido)
    assert len(resultado) == 11


def test_validate_cpf_invalido_tamanho():
    with pytest.raises(CustomException) as exc_info:
        validators.validate_cpf("123456789")  # 9 digitos
    assert exc_info.value.status_code == 422


def test_validate_cpf_invalido_sequencia():
    with pytest.raises(CustomException) as exc_info:
        validators.validate_cpf("11111111111")
    assert exc_info.value.status_code == 422


def test_validate_cpf_invalido_dv():
    with pytest.raises(CustomException) as exc_info:
        # DV incorreto
        validators.validate_cpf("12345678910")
    assert exc_info.value.status_code == 422


def test_validate_cnpj_valido():
    # CNPJ válido conhecido (Exemplo Banco do Brasil)
    cnpj = "00000000000191"
    assert validators.validate_cnpj(cnpj) == cnpj


def test_validate_cnpj_invalido_tamanho():
    with pytest.raises(CustomException) as exc_info:
        validators.validate_cnpj("1234567890123")  # 13 dígitos
    assert exc_info.value.status_code == 422


def test_validate_cnpj_invalido_sequencia():
    with pytest.raises(CustomException) as exc_info:
        validators.validate_cnpj("22222222222222")
    assert exc_info.value.status_code == 422


def test_validate_cnpj_invalido_dv():
    with pytest.raises(CustomException) as exc_info:
        validators.validate_cnpj("00000000000192")  # DV falho
    assert exc_info.value.status_code == 422


def test_validate_cnpj_cpf_wrapper():
    # Função wrapper que escolhe CPF ou CNPJ pelo tamanho
    cpf_valido = generate_cpf()
    assert validators.validate_cnpj_cpf(cpf_valido) == cpf_valido

    cnpj_valido = "00000000000191"
    assert validators.validate_cnpj_cpf(cnpj_valido) == cnpj_valido

    # Tamanho inválido para ambos
    with pytest.raises(CustomException) as exc_info:
        validators.validate_cnpj_cpf("1234")
    assert exc_info.value.status_code == 422

    # None ou Vazio
    assert validators.validate_cnpj_cpf("") == ""
    assert validators.validate_cnpj_cpf(None) is None


# ==========================================
# Testes de Telefone e E-mail
# ==========================================


def test_normalize_phone_valido():
    valido = validators.normalize_phone("(11) 98765-4321")
    assert valido == "11987654321"

    valido2 = validators.normalize_phone("11987654321")
    assert valido2 == "11987654321"

    assert validators.normalize_phone("") == ""
    assert validators.normalize_phone(None) is None


def test_normalize_phone_invalido():
    # Menos que 11 caracteres (depois de limpar)
    with pytest.raises(CustomException) as exc_info:
        validators.normalize_phone("(11) 9876-432")
    assert exc_info.value.status_code == 422

    # Mais que 13 caracteres
    with pytest.raises(CustomException) as exc_info:
        validators.normalize_phone("(11) 98765-4321000")
    assert exc_info.value.status_code == 422


def test_normalize_email_valido():
    assert (
        validators.normalize_email("TeStE@exAmple.com") == "teste@example.com"
    )
    assert validators.normalize_email("") == ""
    assert validators.normalize_email(None) is None


def test_normalize_email_invalido():
    with pytest.raises(CustomException) as exc_info:
        validators.normalize_email("email-invalido")
    assert exc_info.value.status_code == 422

    with pytest.raises(CustomException) as exc_info:
        validators.normalize_email("user@.com")
    assert exc_info.value.status_code == 422
