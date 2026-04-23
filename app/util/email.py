import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from fastapi import Request
from fastapi.templating import Jinja2Templates

from app import core, error

templates = Jinja2Templates(directory=core.settings.TEMPLATES_DIR)


__all__ = ["template_string", "send_email"]


def template_string(template_name: str, content: dict) -> str:
    """Cria uma estring do template a ser utilizado para envio de email

    Args:
        template_name (str): Nome do template a ser usado
        content (dict): conteudo do template

    Returns:
        str: Retorna uma string do template
    """
    content["request"] = Request
    return templates.TemplateResponse(template_name, content).body.decode()


def send_email(email_receiver: str, subject: str, body: str) -> any:
    """Envio de email

    Args:
        email_receiver (str): Email do destinatario
        subject (str): Titulo do Email
        body (str): Conteudo do email obs: aceita template_string

    Raises:
        CustomException: caso nao seja possivel enviar, gera um erro 400
    """
    try:
        em = MIMEMultipart()
        em.attach(MIMEText(body, "html"))
        em["From"] = core.settings.EMAILS_FROM_EMAIL
        em["Subject"] = subject
        em["To"] = email_receiver

        with smtplib.SMTP("smtp.gmail.com", core.settings.SMTP_PORT, timeout=5) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(core.settings.EMAILS_FROM_EMAIL, core.settings.SMTP_PASSWORD)
            smtp.sendmail(
                core.settings.EMAILS_FROM_EMAIL,
                email_receiver,
                em.as_string(),
            )
    except smtplib.SMTPException as e:
        raise error.custom_HTTPException(e)
