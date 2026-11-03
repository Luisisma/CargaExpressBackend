import logging
import smtplib
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from typing import Optional, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)


def _sanitizar_header(valor: str) -> str:
    """Elimina retornos de carro, saltos de línea y comillas accidentales para prevenir CRLF e inyección."""
    if not valor:
        return ""
    return valor.replace("\r", "").replace("\n", "").strip().strip('"').strip("'")


def _enviar_smtp_real(
    destinatario_email: str,
    destinatario_nombre: str,
    asunto: str,
    html_content: str,
    plain_text: Optional[str] = None
) -> Dict[str, Any]:
    """
    Envía un correo electrónico real utilizando un servidor SMTP autenticado con STARTTLS (ej. Gmail).
    Soporta UTF-8 nativo para caracteres latinos (tildes, eñes) en encabezados y cuerpo.
    """
    if not settings.SMTP_HOST or not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        raise ValueError("Configuración SMTP incompleta (se requiere SMTP_HOST, SMTP_USER y SMTP_PASSWORD).")

    email_limpio = _sanitizar_header(destinatario_email)
    nombre_limpio = _sanitizar_header(destinatario_nombre)
    asunto_limpio = _sanitizar_header(asunto)

    remitente_nombre = _sanitizar_header(settings.SMTP_FROM_NAME or "CargaExpress Perú")
    remitente_email = _sanitizar_header(settings.SMTP_FROM_EMAIL or settings.SMTP_USER)

    mensaje = MIMEMultipart("alternative")
    mensaje["Subject"] = Header(asunto_limpio, "utf-8").encode()
    mensaje["From"] = formataddr((str(Header(remitente_nombre, "utf-8")), remitente_email))
    mensaje["To"] = formataddr((str(Header(nombre_limpio, "utf-8")), email_limpio))

    if plain_text:
        mensaje.attach(MIMEText(plain_text, "plain", "utf-8"))
    if html_content:
        mensaje.attach(MIMEText(html_content, "html", "utf-8"))

    password_limpio = settings.SMTP_PASSWORD.replace(" ", "")

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20) as servidor:
        servidor.ehlo()
        servidor.starttls()
        servidor.ehlo()
        servidor.login(settings.SMTP_USER.strip(), password_limpio)
        try:
            servidor.send_message(mensaje)
        except Exception:
            # Fallback seguro con sendmail bytes
            servidor.sendmail(remitente_email, [email_limpio], mensaje.as_bytes())

    logger.info("Correo SMTP enviado exitosamente a %s vía %s", email_limpio, settings.SMTP_HOST)
    return {
        "enviado": True,
        "metodo": "smtp_tls_real",
        "servidor": settings.SMTP_HOST,
        "destinatario": email_limpio
    }


def _enviar_correo_hibrido(
    destinatario_email: str,
    destinatario_nombre: str,
    asunto: str,
    html_content: str,
    plain_text: str,
    categoria: str = "Notificacion General",
    url_adicional: Optional[str] = None
) -> Dict[str, Any]:
    """
    Motor híbrido transaccional (Patrón Estrategia SDD):
    1. Intenta SMTP Real (Gmail STARTTLS) si está configurado en .env.
    2. Fallback a Mailtrap Sandbox API si SMTP falla o no está configurado.
    3. Fallback a consola de desarrollo para no interrumpir el flujo del sistema.
    """
    # 1. Estrategia Principal: SMTP Real (Gmail)
    if settings.EMAIL_ENABLED and settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD:
        try:
            res = _enviar_smtp_real(
                destinatario_email=destinatario_email,
                destinatario_nombre=destinatario_nombre,
                asunto=asunto,
                html_content=html_content,
                plain_text=plain_text
            )
            if url_adicional:
                res["url_adicional"] = url_adicional
            return res
        except Exception as exc:
            logger.warning("Fallo en envío SMTP Real (%s). Conmutando a fallback de seguridad...", exc, exc_info=True)

    # 2. Estrategia Secundaria: Mailtrap Sandbox API
    if settings.MAILTRAP_API_TOKEN:
        try:
            import mailtrap as mt

            mail = mt.Mail(
                sender=mt.Address(email="notificaciones@cargaexpress.pe", name="CargaExpress Notificaciones"),
                to=[mt.Address(email=destinatario_email, name=destinatario_nombre)],
                subject=asunto,
                text=plain_text,
                html=html_content,
                category=categoria
            )

            client = mt.MailtrapClient(
                token=settings.MAILTRAP_API_TOKEN,
                sandbox=True,
                inbox_id=settings.MAILTRAP_INBOX_ID
            )
            client.send(mail)
            logger.info("Correo enviado exitosamente a Mailtrap Inbox %s", settings.MAILTRAP_INBOX_ID)
            return {
                "enviado": True,
                "metodo": "mailtrap_sandbox",
                "inbox_id": settings.MAILTRAP_INBOX_ID,
                "url_adicional": url_adicional
            }
        except Exception as exc:
            logger.error("Error al enviar correo vía Mailtrap: %s", exc)

    # 3. Fallback Seguro: Registro estructurado en consola
    logger.info("Fallback de correo a consola para %s", destinatario_email)
    print("=" * 70)
    print(f" [CORREO SIMULADO - {categoria.upper()}]")
    print(f" Para: {destinatario_email} ({destinatario_nombre})")
    print(f" Asunto: {asunto}")
    if url_adicional:
        print(f" Enlace: {url_adicional}")
    print("=" * 70)

    return {
        "enviado": True,
        "metodo": "consola_fallback",
        "url_adicional": url_adicional
    }


# ==============================================================================
# PLANTILLAS HTML CORPORATIVAS (CSS INLINE / COMPATIBLE CON GMAIL Y OUTLOOK)
# ==============================================================================

def generar_html_recuperacion(nombres: str, reset_url: str, expira_minutos: int = 15) -> str:
    """Construye una plantilla HTML corporativa para el correo de restablecimiento."""
    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Recuperación de Contraseña - CargaExpress</title>
    </head>
    <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; margin: 0; padding: 20px; color: #2b2d42;">
        <div style="max-width: 580px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.08); border: 1px solid #e2e8f0;">
            <div style="background: linear-gradient(135deg, #0d3b66 0%, #1d3557 100%); padding: 30px 25px; text-align: center; color: #ffffff;">
                <h1 style="margin: 0; font-size: 24px; letter-spacing: 1px; font-weight: 700;">CARGAEXPRESS PERÚ</h1>
                <p style="margin: 5px 0 0 0; color: #f4a261; font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Sistema Integrado de Envíos y Logística</p>
            </div>
            <div style="padding: 30px 28px; line-height: 1.6;">
                <div style="font-size: 18px; font-weight: 600; color: #1e293b; margin-bottom: 12px;">Hola, {nombres}</div>
                <p>Recibimos una solicitud para restablecer la contraseña de acceso a tu cuenta en la plataforma institucional.</p>
                <p>Para crear una nueva contraseña segura, haz clic en el siguiente botón:</p>
                <div style="text-align: center; margin: 32px 0;">
                    <a href="{reset_url}" style="background: #e63946; color: #ffffff !important; padding: 14px 28px; font-size: 15px; font-weight: 600; text-decoration: none; border-radius: 8px; display: inline-block; box-shadow: 0 4px 12px rgba(230, 57, 70, 0.35);" target="_blank">
                        Restablecer Mi Contraseña
                    </a>
                </div>
                <div style="background-color: #f8fafc; border-left: 4px solid #f4a261; padding: 12px 16px; border-radius: 4px; font-size: 13px; color: #475569; margin-top: 24px;">
                    <strong>Información de Seguridad:</strong>
                    <ul style="margin: 6px 0 0 0; padding-left: 20px;">
                        <li>Este enlace es de uso único y expirará en <strong>{expira_minutos} minutos</strong>.</li>
                        <li>Si tú no solicitaste este cambio, puedes ignorar este mensaje de forma segura. Tu contraseña actual no será modificada.</li>
                    </ul>
                </div>
                <p style="margin-top: 24px; font-size: 12px; color: #64748b;">
                    Si el botón no funciona, copia y pega el siguiente enlace en tu navegador:<br>
                    <a href="{reset_url}" style="word-break: break-all; font-size: 12px; color: #0d3b66;">{reset_url}</a>
                </p>
            </div>
            <div style="background-color: #f1f5f9; padding: 18px 25px; text-align: center; font-size: 12px; color: #64748b; border-top: 1px solid #e2e8f0;">
                &copy; CargaExpress Perú S.A.C. RUC 20100227461.<br>
                Este es un mensaje automático de seguridad, por favor no responda a este remitente.
            </div>
        </div>
    </body>
    </html>
    """


def generar_html_preregistro(
    remitente_nombre: str,
    codigo_tracking: str,
    origen_nombre: str,
    destino_nombre: str,
    tarifa_estimada: float,
    tipo_paquete: str
) -> str:
    """Plantilla de confirmación del pre-registro web de encomienda."""
    tracking_url = f"{settings.FRONTEND_URL}/tracking/{codigo_tracking}"
    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head><meta charset="UTF-8"><title>Pre-registro Exitoso - CargaExpress</title></head>
    <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8fafc; margin: 0; padding: 20px; color: #1e293b;">
        <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.06); border: 1px solid #e2e8f0;">
            <div style="background: #1a365d; padding: 26px 24px; text-align: center; color: #ffffff;">
                <h2 style="margin: 0; font-size: 22px; font-weight: 700;">CARGAEXPRESS PERÚ</h2>
                <p style="margin: 4px 0 0 0; color: #cbd5e1; font-size: 13px;">Confirmación de Pre-registro de Encomienda</p>
            </div>
            <div style="padding: 28px 24px;">
                <h3 style="margin-top: 0; color: #0f172a;">¡Hola, {remitente_nombre}!</h3>
                <p style="color: #475569; font-size: 14px; line-height: 1.6;">
                    Tu pre-orden ha sido registrada exitosamente en nuestro sistema. Presenta el siguiente código de seguimiento en la ventanilla de la agencia para el pesaje en balanza y formalización del envío:
                </p>
                <div style="background: #f1f5f9; border: 2px dashed #0284c7; border-radius: 8px; padding: 18px; text-align: center; margin: 20px 0;">
                    <div style="font-size: 12px; color: #64748b; text-transform: uppercase; font-weight: 600; letter-spacing: 1px;">Código de Seguimiento</div>
                    <div style="font-size: 26px; font-weight: 800; color: #0284c7; letter-spacing: 2px; margin: 4px 0;">{codigo_tracking}</div>
                    <small style="color: #64748b;">Muestra este código al cajero para atención prioritaria</small>
                </div>
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 14px;">
                    <tr style="border-bottom: 1px solid #f1f5f9;"><td style="padding: 8px 0; color: #64748b;">Ruta:</td><td style="padding: 8px 0; text-align: right; font-weight: 600;">{origen_nombre} ➔ {destino_nombre}</td></tr>
                    <tr style="border-bottom: 1px solid #f1f5f9;"><td style="padding: 8px 0; color: #64748b;">Tipo de Carga:</td><td style="padding: 8px 0; text-align: right; font-weight: 600;">{tipo_paquete.upper()}</td></tr>
                    <tr><td style="padding: 8px 0; color: #64748b;">Tarifa Estimada:</td><td style="padding: 8px 0; text-align: right; font-weight: 700; color: #16a34a; font-size: 16px;">S/ {tarifa_estimada:.2f}</td></tr>
                </table>
                <div style="text-align: center; margin: 26px 0;">
                    <a href="{tracking_url}" style="background: #0284c7; color: #ffffff !important; padding: 12px 24px; font-size: 14px; font-weight: 600; text-decoration: none; border-radius: 6px; display: inline-block;">
                        Rastrear Estado de Encomienda
                    </a>
                </div>
            </div>
            <div style="background-color: #f8fafc; padding: 16px; text-align: center; font-size: 12px; color: #94a3b8; border-top: 1px solid #e2e8f0;">
                CargaExpress Perú S.A.C. · Envíos seguros a nivel nacional
            </div>
        </div>
    </body>
    </html>
    """


def generar_html_cambio_estado(
    destinatario_nombre: str,
    codigo_tracking: str,
    nuevo_estado: str,
    descripcion: str,
    ubicacion: Optional[str] = None
) -> str:
    """Plantilla corporativa para notificaciones de cambio de estado en la cadena de custodia."""
    tracking_url = f"{settings.FRONTEND_URL}/tracking/{codigo_tracking}"
    estado_key = nuevo_estado.replace(" ", "_").upper()

    colores = {
        "RECEPCIONADO": ("#0284c7", "Paquete Admitido en Origen"),
        "EN_RUTA": ("#ea580c", "En Tránsito Interprovincial"),
        "EN_AGENCIA_DESTINO": ("#ca8a04", "Listo para Retiro en Destino"),
        "EN_REPARTO": ("#2563eb", "En Reparto Domiciliario"),
        "ENTREGADO": ("#16a34a", "Encomienda Entregada Conforme"),
        "CANCELADO": ("#dc2626", "Envío Anulado"),
        "SINIESTRADO": ("#dc2626", "Incidencia Grave / Siniestro")
    }
    color_hex, estado_titulo = colores.get(estado_key, ("#1a365d", estado_key))

    ubicacion_html = f"""
    <tr style="border-bottom: 1px solid #f1f5f9;">
        <td style="padding: 10px 0; color: #64748b;">Ubicación Actual:</td>
        <td style="padding: 10px 0; text-align: right; font-weight: 600; color: #1e293b;">{ubicacion}</td>
    </tr>
    """ if ubicacion else ""

    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head><meta charset="UTF-8"><title>Actualización de Envío - CargaExpress</title></head>
    <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8fafc; margin: 0; padding: 20px; color: #1e293b;">
        <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.06); border: 1px solid #e2e8f0;">
            <div style="background: #1a365d; padding: 24px; text-align: center; color: #ffffff;">
                <h2 style="margin: 0; font-size: 20px; font-weight: 700; letter-spacing: 0.5px;">CARGAEXPRESS PERÚ</h2>
                <p style="margin: 4px 0 0 0; color: #cbd5e1; font-size: 13px;">Actualización de Estado de Encomienda</p>
            </div>
            <div style="padding: 28px 24px;">
                <h3 style="margin-top: 0; color: #0f172a;">Estimado/a {destinatario_nombre},</h3>
                <p style="color: #475569; font-size: 14px; line-height: 1.6;">
                    Te informamos que tu envío con código <strong>{codigo_tracking}</strong> ha actualizado su estado en la cadena logística:
                </p>

                <div style="text-align: center; margin: 24px 0;">
                    <span style="background-color: {color_hex}; color: #ffffff; font-size: 15px; font-weight: 700; padding: 8px 20px; border-radius: 20px; display: inline-block; letter-spacing: 0.5px;">
                        {estado_titulo.upper()}
                    </span>
                </div>

                <div style="background: #f8fafc; border-left: 4px solid {color_hex}; padding: 14px 18px; border-radius: 6px; margin: 20px 0; font-size: 14px; color: #334155;">
                    <strong>Detalle del Hito:</strong>
                    <div style="margin-top: 4px; color: #475569;">{descripcion}</div>
                </div>

                <table style="width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 14px;">
                    <tr style="border-bottom: 1px solid #f1f5f9;">
                        <td style="padding: 10px 0; color: #64748b;">Código de Rastreo:</td>
                        <td style="padding: 10px 0; text-align: right; font-weight: 700; color: #0284c7;">{codigo_tracking}</td>
                    </tr>
                    {ubicacion_html}
                </table>

                <div style="text-align: center; margin: 28px 0 10px 0;">
                    <a href="{tracking_url}" style="background: #1a365d; color: #ffffff !important; padding: 12px 26px; font-size: 14px; font-weight: 600; text-decoration: none; border-radius: 6px; display: inline-block;">
                        Ver Seguimiento en Tiempo Real
                    </a>
                </div>
            </div>
            <div style="background-color: #f8fafc; padding: 16px; text-align: center; font-size: 12px; color: #94a3b8; border-top: 1px solid #e2e8f0;">
                CargaExpress Perú S.A.C. · Sistema Automatizado de Trazabilidad Logística
            </div>
        </div>
    </body>
    </html>
    """


# ==============================================================================
# DISPARADORES PÚBLICOS DEL SISTEMA
# ==============================================================================

def enviar_correo_recuperacion(
    destinatario_email: str,
    destinatario_nombre: str,
    token: str
) -> Dict[str, Any]:
    """Envía el correo de restablecimiento de contraseña mediante el motor híbrido."""
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

    return _enviar_correo_hibrido(
        destinatario_email=destinatario_email,
        destinatario_nombre=destinatario_nombre,
        asunto="CargaExpress - Restablecimiento de Contraseña",
        html_content=html_content,
        plain_text=plain_text,
        categoria="Recuperacion Password",
        url_adicional=reset_url
    )


def enviar_correo_preregistro(
    destinatario_email: str,
    destinatario_nombre: str,
    codigo_tracking: str,
    origen_nombre: str,
    destino_nombre: str,
    tarifa_estimada: float,
    tipo_paquete: str
) -> Dict[str, Any]:
    """Envía la notificación de pre-registro web exitoso al remitente."""
    html_content = generar_html_preregistro(
        remitente_nombre=destinatario_nombre,
        codigo_tracking=codigo_tracking,
        origen_nombre=origen_nombre,
        destino_nombre=destino_nombre,
        tarifa_estimada=tarifa_estimada,
        tipo_paquete=tipo_paquete
    )
    plain_text = (
        f"Hola {destinatario_nombre},\n\n"
        f"Tu pre-orden de encomienda ha sido registrada con éxito en CargaExpress.\n"
        f"Código de Seguimiento: {codigo_tracking}\n"
        f"Ruta: {origen_nombre} -> {destino_nombre}\n"
        f"Tarifa Estimada: S/ {tarifa_estimada:.2f}\n\n"
        f"Presenta este código en la agencia de origen para el pesaje oficial.\n"
        f"Rastreo: {settings.FRONTEND_URL}/tracking/{codigo_tracking}"
    )

    return _enviar_correo_hibrido(
        destinatario_email=destinatario_email,
        destinatario_nombre=destinatario_nombre,
        asunto=f"CargaExpress - Pre-registro Exitoso [{codigo_tracking}]",
        html_content=html_content,
        plain_text=plain_text,
        categoria="Pre-registro Encomienda"
    )


def generar_html_preregistro_destinatario(
    destinatario_nombre: str,
    remitente_nombre: str,
    codigo_tracking: str,
    origen_nombre: str,
    destino_nombre: str,
    tipo_paquete: str
) -> str:
    """Plantilla de aviso al destinatario cuando se genera una pre-orden dirigida a él."""
    tracking_url = f"{settings.FRONTEND_URL}/tracking/{codigo_tracking}"
    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head><meta charset="UTF-8"><title>Envío en Camino - CargaExpress</title></head>
    <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8fafc; margin: 0; padding: 20px; color: #1e293b;">
        <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.06); border: 1px solid #e2e8f0;">
            <div style="background: #1a365d; padding: 26px 24px; text-align: center; color: #ffffff;">
                <h2 style="margin: 0; font-size: 22px; font-weight: 700;">CARGAEXPRESS PERÚ</h2>
                <p style="margin: 4px 0 0 0; color: #cbd5e1; font-size: 13px;">Notificación de Envío Programado</p>
            </div>
            <div style="padding: 28px 24px;">
                <h3 style="margin-top: 0; color: #0f172a;">¡Hola, {destinatario_nombre}!</h3>
                <p style="color: #475569; font-size: 14px; line-height: 1.6;">
                    Te informamos que <strong>{remitente_nombre}</strong> ha registrado una encomienda dirigida a ti a través de nuestra plataforma web.
                </p>
                <div style="background: #f1f5f9; border: 2px dashed #0284c7; border-radius: 8px; padding: 18px; text-align: center; margin: 20px 0;">
                    <div style="font-size: 12px; color: #64748b; text-transform: uppercase; font-weight: 600; letter-spacing: 1px;">Código de Seguimiento</div>
                    <div style="font-size: 26px; font-weight: 800; color: #0284c7; letter-spacing: 2px; margin: 4px 0;">{codigo_tracking}</div>
                    <small style="color: #64748b;">Podrás rastrear el avance en tiempo real con este código</small>
                </div>
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 14px;">
                    <tr style="border-bottom: 1px solid #f1f5f9;"><td style="padding: 8px 0; color: #64748b;">Remitente:</td><td style="padding: 8px 0; text-align: right; font-weight: 600;">{remitente_nombre}</td></tr>
                    <tr style="border-bottom: 1px solid #f1f5f9;"><td style="padding: 8px 0; color: #64748b;">Ruta:</td><td style="padding: 8px 0; text-align: right; font-weight: 600;">{origen_nombre} ➔ {destino_nombre}</td></tr>
                    <tr><td style="padding: 8px 0; color: #64748b;">Tipo de Carga:</td><td style="padding: 8px 0; text-align: right; font-weight: 600;">{tipo_paquete.upper()}</td></tr>
                </table>
                <div style="text-align: center; margin: 26px 0;">
                    <a href="{tracking_url}" style="background: #0284c7; color: #ffffff !important; padding: 12px 24px; font-size: 14px; font-weight: 600; text-decoration: none; border-radius: 6px; display: inline-block;">
                        Rastrear Estado de Encomienda
                    </a>
                </div>
            </div>
            <div style="background-color: #f8fafc; padding: 16px; text-align: center; font-size: 12px; color: #94a3b8; border-top: 1px solid #e2e8f0;">
                CargaExpress Perú S.A.C. · Envíos seguros a nivel nacional
            </div>
        </div>
    </body>
    </html>
    """


def enviar_correo_preregistro_destinatario(
    destinatario_email: str,
    destinatario_nombre: str,
    remitente_nombre: str,
    codigo_tracking: str,
    origen_nombre: str,
    destino_nombre: str,
    tipo_paquete: str
) -> Dict[str, Any]:
    """Envía la notificación de pre-registro al destinatario."""
    html_content = generar_html_preregistro_destinatario(
        destinatario_nombre=destinatario_nombre,
        remitente_nombre=remitente_nombre,
        codigo_tracking=codigo_tracking,
        origen_nombre=origen_nombre,
        destino_nombre=destino_nombre,
        tipo_paquete=tipo_paquete
    )
    plain_text = (
        f"Hola {destinatario_nombre},\n\n"
        f"{remitente_nombre} ha registrado un envío para ti en CargaExpress.\n"
        f"Código de Seguimiento: {codigo_tracking}\n"
        f"Ruta: {origen_nombre} -> {destino_nombre}\n"
        f"Tipo de Carga: {tipo_paquete.upper()}\n\n"
        f"Podrás rastrear el envío cuando sea entregado en agencia:\n"
        f"{settings.FRONTEND_URL}/tracking/{codigo_tracking}"
    )

    return _enviar_correo_hibrido(
        destinatario_email=destinatario_email,
        destinatario_nombre=destinatario_nombre,
        asunto=f"CargaExpress - Envío programado para ti por {remitente_nombre} [{codigo_tracking}]",
        html_content=html_content,
        plain_text=plain_text,
        categoria="Aviso Encomienda Destinatario"
    )


def enviar_correo_cambio_estado(
    destinatario_email: str,
    destinatario_nombre: str,
    codigo_tracking: str,
    nuevo_estado: str,
    descripcion: str,
    ubicacion: Optional[str] = None
) -> Dict[str, Any]:
    """Envía la notificación de actualización de estado logístico en tiempo real."""
    html_content = generar_html_cambio_estado(
        destinatario_nombre=destinatario_nombre,
        codigo_tracking=codigo_tracking,
        nuevo_estado=nuevo_estado,
        descripcion=descripcion,
        ubicacion=ubicacion
    )
    plain_text = (
        f"Hola {destinatario_nombre},\n\n"
        f"Tu envío {codigo_tracking} ha cambiado a estado: {nuevo_estado.replace('_', ' ').upper()}.\n"
        f"Detalle: {descripcion}\n"
        f"{f'Ubicación: {ubicacion}' if ubicacion else ''}\n\n"
        f"Rastreo en vivo: {settings.FRONTEND_URL}/tracking/{codigo_tracking}"
    )

    return _enviar_correo_hibrido(
        destinatario_email=destinatario_email,
        destinatario_nombre=destinatario_nombre,
        asunto=f"CargaExpress - Actualización de Envío [{codigo_tracking}]: {nuevo_estado.replace('_', ' ').upper()}",
        html_content=html_content,
        plain_text=plain_text,
        categoria="Cambio de Estado Encomienda"
    )

