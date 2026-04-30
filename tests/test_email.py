# tests/test_email.py
"""
Testes unitários do módulo de email (app/util/email.py).

Usa mocks para evitar conexão SMTP real durante os testes.
"""

import smtplib
from unittest.mock import MagicMock, patch

import pytest

from app import error
from app.util.email import send_email, template_string

# ---------------------------------------------------------------------------
# template_string
# ---------------------------------------------------------------------------


def test_template_string_renderiza_conteudo():
    """template_string deve renderizar o template com as variáveis fornecidas."""
    result = template_string("reset_password.html", {"code": "AB1234"})

    assert isinstance(result, str)
    assert "AB1234" in result


# ---------------------------------------------------------------------------
# send_email
# ---------------------------------------------------------------------------


@patch("app.util.email.smtplib.SMTP")
def test_send_email_com_sucesso(mock_smtp_class):
    """send_email com mock SMTP deve executar sem erros."""
    mock_smtp_instance = MagicMock()
    mock_smtp_class.return_value.__enter__ = MagicMock(
        return_value=mock_smtp_instance
    )
    mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)

    # Não deve lançar exceção
    send_email("destinatario@teste.com", "Assunto Teste", "<p>Corpo</p>")

    mock_smtp_instance.ehlo.assert_called_once()
    mock_smtp_instance.starttls.assert_called_once()
    mock_smtp_instance.login.assert_called_once()
    mock_smtp_instance.sendmail.assert_called_once()


@patch("app.util.email.smtplib.SMTP")
def test_send_email_falha_smtp_levanta_custom_exception(mock_smtp_class):
    """Falha no SMTP deve lançar CustomException 500."""
    mock_smtp_class.side_effect = smtplib.SMTPException("Falha de conexão")

    with pytest.raises(error.CustomException) as exc_info:
        send_email("destinatario@teste.com", "Assunto", "<p>Corpo</p>")

    assert exc_info.value.status_code == 500
    assert "e-mail" in exc_info.value.detail
