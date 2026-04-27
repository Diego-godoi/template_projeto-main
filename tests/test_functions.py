# tests/test_functions.py
"""
Testes abrangentes dos utilitários lógicos do sistema (conversões de formatos de cases e códigos numéricos).
"""

import os

import pytest
from fastapi import UploadFile

from app.error import CustomException
from app.util import functions

# ==========================================
# Testes de Conversão de Casos (Formatadores de Strings)
# ==========================================


def test_pascal_to_camel_case():
    assert (
        functions.pascal_to_camel_case("MinhaClassePascal")
        == "minhaClassePascal"
    )
    assert functions.pascal_to_camel_case("UmaPalavra") == "umaPalavra"
    assert functions.pascal_to_camel_case("A") == "a"


def test_pascal_to_snake_case():
    # O script atual insere '_' antes das maiúsculas e passa para minúsculo
    assert (
        functions.pascal_to_snake_case("MinhaClassePascal")
        == "minha_classe_pascal"
    )
    assert functions.pascal_to_snake_case("Uma") == "uma"


def test_snake_to_pascal_case():
    assert (
        functions.snake_to_pascal_case("minha_classe_pascal")
        == "MinhaClassePascal"
    )
    assert functions.snake_to_pascal_case("uma") == "Uma"
    # Também converte se for uma única palavra iniciada em minúscula
    assert functions.snake_to_pascal_case("variável") == "Variável"


def test_pascal_to_kebab_case():
    assert (
        functions.pascal_to_kebab_case("MinhaClassePascal")
        == "minha-classe-pascal"
    )
    assert functions.pascal_to_kebab_case("Uma") == "uma"


def test_camel_to_kebab():
    assert functions.camel_to_kebab("minhaClasseCamel") == "minha-classe-camel"
    assert functions.camel_to_kebab("simples") == "simples"


def test_camel_to_snake_case():
    assert (
        functions.camel_to_snake_case("minhaClasseCamel")
        == "minha_classe_camel"
    )
    assert functions.camel_to_snake_case("simples") == "simples"


# ==========================================
# Testes de Geração Aletatória
# ==========================================


def test_generate_code_format():
    """Verifica formato de código para emails (ex: AB1234)"""
    codigo = functions.generate_code()

    assert type(codigo) == str
    assert len(codigo) == 6
    # Primeiros dois são letras maiúsculas
    assert codigo[:2].isalpha() and codigo[:2].isupper()
    # Últimos quatro são números
    assert codigo[2:].isdigit()


def test_generate_cpf_validez():
    """Garante que a função geradora de CPF (usada em seeds) gera de fato CPFs VÁLIDOS"""
    from app.util.validators import validate_cpf

    cpf_gerado = functions.generate_cpf()
    assert len(cpf_gerado) == 11

    # Se invalidar, a função levanta CustomException 422
    assert validate_cpf(cpf_gerado) == cpf_gerado


# ==========================================
# Testes de I/O e Manipulação de Arquivos
# ==========================================


def test_save_file_video_sucesso(monkeypatch, tmp_path):
    """Testa salvar um arquivo de vídeo autêntico apontando para temp_dir."""
    monkeypatch.setattr(
        "app.util.functions.settings.UPLOAD_DIR", str(tmp_path)
    )

    video_path = "tests/file_test/video.mp4"
    # Certificar-se que o arquivo existe para não quebrar localmente
    if not os.path.exists(video_path):
        pytest.skip(
            f"Arquivo de mock {video_path} não encontrado, pulando teste."
        )

    with open(video_path, "rb") as f:
        # UploadFile do FastAPI
        file_mock = UploadFile(filename="video.mp4", file=f)
        try:
            saved_name = functions.save_file(file_mock, "video")
            assert saved_name is not None
            assert os.path.exists(os.path.join(str(tmp_path), saved_name))
        finally:
            file_mock.file.close()


def test_save_file_formato_invalido(monkeypatch, tmp_path):
    """Tentando passar o vídeo mas pedindo validação de imagem deve falhar."""
    monkeypatch.setattr(
        "app.util.functions.settings.UPLOAD_DIR", str(tmp_path)
    )
    video_path = "tests/file_test/video.mp4"

    if not os.path.exists(video_path):
        pytest.skip(f"Arquivo de mock {video_path} não encontrado.")

    with open(video_path, "rb") as f:
        file_mock = UploadFile(filename="video.mp4", file=f)
        with pytest.raises(CustomException) as exc_info:
            functions.save_file(
                file_mock, "image"
            )  # magic.from_buffer detectará "video"

        assert exc_info.value.status_code == 422
        assert "Formato de media invalido" in exc_info.value.detail


def test_save_file_dir_nao_encontrado(monkeypatch):
    """Garante que a função aborte se UPLOAD_DIR for inválido."""
    monkeypatch.setattr(
        "app.util.functions.settings.UPLOAD_DIR", "/dir/inexistente/invalido"
    )

    with pytest.raises(CustomException) as exc_info:
        file_mock = UploadFile(
            filename="teste.txt", file=open(os.devnull, "rb")
        )
        functions.save_file(file_mock, "video")

    assert exc_info.value.status_code == 400
    assert "diretorio não encontrado" in exc_info.value.detail


def test_delete_file_e_list_files_sucesso(monkeypatch, tmp_path):
    """Testa criação, listagem e exclusão atômica em tmp_path."""
    test_dir = str(tmp_path) + "/"
    # Criar um arquivo dummy manual
    with open(test_dir + "dummy.txt", "w") as f:
        f.write("mock")

    # Conferir se lista
    files = functions.list_files(test_dir)
    assert "dummy.txt" in files
    assert len(files) == 1

    # Deletar arquivo
    sucesso = functions.delete_file(test_dir, "dummy.txt")
    assert sucesso is True

    # Garantir que sumiu
    assert len(functions.list_files(test_dir)) == 0


def test_delete_file_inexistente():
    """Garante CustomException 404 ao tentar deletar arquivo fantasma."""
    with pytest.raises(CustomException) as exc_info:
        functions.delete_file("/caminho/invalido/", "dummy.txt")

    assert exc_info.value.status_code == 404
