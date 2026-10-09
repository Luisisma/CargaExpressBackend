import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


def generar_html_recuperacion(nombres: str, reset_url: str, expira_minutos: int = 15) -> str:
    """Construye una plantilla HTML corporativa para el correo de restablecimiento."""
    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Recuperación de Contraseña - CargaExpress</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f4f7f6;
                margin: 0;
                padding: 20px;
                color: #2b2d42;
            }}
            .email-card {{
                max-width: 580px;
                margin: 0 auto;
                background: #ffffff;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 4px 15px rgba(0,0,0,0.08);
                border: 1px solid #e2e8f0;
            }}
            .header {{
                background: linear-gradient(135deg, #0d3b66 0%, #1d3557 100%);
                padding: 30px 25px;
                text-align: center;
                color: #ffffff;
            }}
            .header h1 {{
                margin: 0;
                font-size: 24px;
                letter-spacing: 1px;
                font-weight: 700;
            }}
            .header p {{
                margin: 5px 0 0 0;
                color: #f4a261;
                font-size: 13px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            .body-content {{
                padding: 30px 28px;
                line-height: 1.6;
            }}
            .greeting {{
                font-size: 18px;
                font-weight: 600;
                color: #1e293b;
                margin-bottom: 12px;
            }}
            .btn-container {{
                text-align: center;
                margin: 32px 0;
            }}
            .btn-reset {{
                background: linear-gradient(135deg, #e63946 0%, #d90429 100%);
                color: #ffffff !important;
                padding: 14px 28px;
                font-size: 15px;
                font-weight: 600;
                text-decoration: none;
                border-radius: 8px;
                display: inline-block;
                box-shadow: 0 4px 12px rgba(230, 57, 70, 0.35);
            }}
            .security-box {{
                background-color: #f8fafc;
                border-left: 4px solid #f4a261;
                padding: 12px 16px;
                border-radius: 4px;
                font-size: 13px;
                color: #475569;
                margin-top: 24px;
            }}
            .footer {{
                background-color: #f1f5f9;
                padding: 18px 25px;
                text-align: center;
                font-size: 12px;
                color: #64748b;
                border-top: 1px solid #e2e8f0;
            }}
            .link-alt {{
                word-break: break-all;
                font-size: 12px;
                color: #0d3b66;
            }}
        </style>
    </head>
    <body>
        <div class="email-card">
            <div class="header">
                <h1>CARGAEXPRESS PERÚ</h1>
                <p>Sistema Integrado de Envíos y Logística</p>
            </div>
            <div class="body-content">
                <div class="greeting">Hola, {nombres}</div>
                <p>
                    Recibimos una solicitud para restablecer la contraseña de acceso a tu cuenta en el sistema institucional.
                </p>
                <p>
                    Para crear una nueva contraseña segura, haz clic en el siguiente botón:
                </p>
                <div class="btn-container">
                    <a href="{reset_url}" class="btn-reset" target="_blank">
                        Restablecer Mi Contraseña
                    </a>
                </div>
                <div class="security-box">
                    <strong>Información de Seguridad:</strong>
                    <ul style="margin: 6px 0 0 0; padding-left: 20px;">
                        <li>Este enlace es de uso único y expirará en <strong>{expira_minutos} minutos</strong>.</li>
                        <li>Si tú no solicitaste este cambio, puedes ignorar este mensaje de forma segura. Tu contraseña actual no será modificada.</li>
                    </ul>
                </div>
                <p style="margin-top: 24px; font-size: 12px; color: #64748b;">
                    Si el botón no funciona, copia y pega el siguiente enlace en tu navegador:
                    <br>
                    <a href="{reset_url}" class="link-alt">{reset_url}</a>
                </p>
            </div>
            <div class="footer">
                &copy; CargaExpress Perú. Plataforma de Seguridad y Control Operativo.<br>
                Este es un mensaje automático de seguridad, por favor no responda a este remitente.
            </div>
        </div>
    </body>
    </html>
    """


def enviar_correo_recuperacion(
    destinatario_email: str,
    destinatario_nombre: str,
    token: str
) -> dict:
    """
    Envía el correo de restablecimiento usando la API oficial de Mailtrap Sandbox.
    Si Mailtrap no está configurado o falla, registra el enlace en consola para testing.
    """
    reset_url = f"{settings.FRONTEND_URL}/auth/restablecer-password?token={token}"
    html_content = generar_html_recuperacion(
        nombres=destinatario_nombre,
        reset_url=reset_url,
        expira_minutos=settings.RESET_TOKEN_EXPIRE_MINUTES
    )
    plain_text = (
        f"Hola {destinatario_nombre},\n\n"
        f"Para restablecer tu contraseña en CargaExpress Perú, visita el siguiente enlace:\n"
        f"{reset_url}\n\n"
        f"Este enlace expirará en {settings.RESET_TOKEN_EXPIRE_MINUTES} minutos.\n"
        f"Si no solicitaste este cambio, puedes ignorar este mensaje."
    )

    # Si se configuró el token de Mailtrap en .env
    if settings.MAILTRAP_API_TOKEN:
        try:
            import mailtrap as mt

            mail = mt.Mail(
                sender=mt.Address(email="seguridad@cargaexpress.pe", name="CargaExpress Seguridad"),
                to=[mt.Address(email=destinatario_email, name=destinatario_nombre)],
                subject="CargaExpress - Restablecimiento de Contraseña",
                text=plain_text,
                html=html_content,
                category="Recuperacion Password"
            )

            client = mt.MailtrapClient(
                token=settings.MAILTRAP_API_TOKEN,
                sandbox=True,
                inbox_id=settings.MAILTRAP_INBOX_ID
            )
            response = client.send(mail)
            logger.info("Correo enviado exitosamente a Mailtrap Inbox %s: %s", settings.MAILTRAP_INBOX_ID, response)
            return {
                "enviado": True,
                "metodo": "mailtrap_sandbox",
                "inbox_id": settings.MAILTRAP_INBOX_ID,
                "reset_url": reset_url
            }
        except Exception as exc:
            logger.error("Error al enviar correo vía Mailtrap: %s", exc, exc_info=True)

    # Fallback de desarrollo a consola
    logger.warning("Mailtrap no disponible o fallo de red. Fallback a consola:")
    print("=" * 70)
    print(" [CORREO SIMULADO DE RECUPERACIÓN - CARGAEXPRESS]")
    print(f" Para: {destinatario_email} ({destinatario_nombre})")
    print(f" Enlace de restablecimiento:\n {reset_url}")
    print("=" * 70)

    return {
        "enviado": True,
        "metodo": "consola_fallback",
        "reset_url": reset_url
    }
