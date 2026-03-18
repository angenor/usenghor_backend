"""
Service d'envoi d'email
=======================

Envoi d'emails transactionnels via SMTP (Gmail) avec aiosmtplib.
"""

import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import aiosmtplib
from jinja2 import Environment, FileSystemLoader

from app.config import settings

logger = logging.getLogger(__name__)

# Dossier des templates email
TEMPLATES_DIR = Path(__file__).parent.parent / "templates" / "email"

# Environnement Jinja2 pour les templates email
_jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=True,
)


class EmailService:
    """Service d'envoi d'email via SMTP Gmail."""

    @staticmethod
    async def send_email(
        to: str | list[str],
        subject: str,
        template_name: str | None = None,
        context: dict | None = None,
        html_content: str | None = None,
    ) -> bool:
        """
        Envoie un email via SMTP Gmail.

        Args:
            to: Destinataire(s)
            subject: Sujet de l'email
            template_name: Nom du template Jinja2 (sans extension)
            context: Variables pour le template
            html_content: Contenu HTML direct (alternative au template)

        Returns:
            True si envoyé avec succès, False sinon.
        """
        if not settings.smtp_password:
            logger.error("SMTP_PASSWORD non configuré — email non envoyé")
            return False

        # Générer le HTML depuis le template ou le contenu direct
        if template_name:
            try:
                template = _jinja_env.get_template(f"{template_name}.html")
                body_html = template.render(**(context or {}))
            except Exception:
                logger.exception("Erreur lors du rendu du template '%s'", template_name)
                return False
        elif html_content:
            body_html = html_content
        else:
            logger.error("Ni template_name ni html_content fourni")
            return False

        # Préparer les destinataires
        recipients = [to] if isinstance(to, str) else to

        # Construire le message MIME
        msg = MIMEMultipart("alternative")
        msg["From"] = settings.smtp_from_email
        msg["To"] = ", ".join(recipients)
        msg["Subject"] = subject
        msg.attach(MIMEText(body_html, "html", "utf-8"))

        try:
            await aiosmtplib.send(
                msg,
                hostname=settings.smtp_host,
                port=settings.smtp_port,
                username=settings.smtp_user,
                password=settings.smtp_password,
                start_tls=True,
            )
            logger.info(
                "Email envoyé avec succès à %s (sujet: %s)",
                ", ".join(recipients),
                subject,
            )
            return True
        except Exception:
            logger.exception(
                "Erreur lors de l'envoi de l'email à %s",
                ", ".join(recipients),
            )
            return False
