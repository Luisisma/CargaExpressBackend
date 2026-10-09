import re
import logging
from typing import Dict, Any, Optional
from html import unescape
import httpx

logger = logging.getLogger(__name__)

RENIEC_DNI_URL = "http://martinnauca.com/api/reniec/dni/{dni}"
SUNAT_RUC_URL = "https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/jcrS00Alias"

SUNAT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
    ),
    "Content-Type": "application/x-www-form-urlencoded",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

RUC_LABEL_MAPPING = {
    "numero de ruc": "numero_ruc",
    "ruc": "numero_ruc",
    "tipo contribuyente": "tipo_contribuyente",
    "nombre comercial": "nombre_comercial",
    "fecha de inscripcion": "fecha_inscripcion",
    "fecha de inicio de actividades": "fecha_inicio_actividades",
    "estado": "estado_contribuyente",
    "estado del contribuyente": "estado_contribuyente",
    "condicion": "condicion_contribuyente",
    "condicion del contribuyente": "condicion_contribuyente",
    "domicilio fiscal": "domicilio_fiscal",
}


def _clean_ruc_text(value: str) -> str:
    val = unescape(value or "")
    val = re.sub(r"(?is)<option\b[^>]*>", "\n", val)
    val = re.sub(r"(?is)</option>", "\n", val)
    val = re.sub(r"<br\s*/?>", "\n", val, flags=re.I)
    val = re.sub(r"<[^>]+>", " ", val)
    val = val.replace("\xa0", " ")
    lines = [re.sub(r"[\t\r\n ]+", " ", l).strip() for l in val.splitlines() if re.sub(r"[\t\r\n ]+", " ", l).strip()]
    return "\n".join(lines) if lines else re.sub(r"[\t\r\n ]+", " ", val).strip()


def _normalize_ruc_label(label: str) -> str:
    lbl = _clean_ruc_text(label).strip(" :")
    for src, dst in {"á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ñ": "n"}.items():
        lbl = lbl.replace(src, dst).replace(src.upper(), dst.upper())
    return re.sub(r"\s+", " ", lbl).lower()


def _extract_ruc_legacy_table(raw_html: str) -> Dict[str, str]:
    cells = []
    for attrs, content in re.findall(r"(?is)<td\b([^>]*)>(.*?)</td>", re.sub(r"(?is)<!--.*?-->", " ", raw_html or "")):
        class_match = re.search(r"""class\s*=\s*["']?([^"'\s>]+)""", attrs, re.I)
        class_name = class_match.group(1).lower() if class_match else ""
        text = _clean_ruc_text(content)
        if text:
            cells.append((class_name, text))
    vals = {}
    i = 0
    while i < len(cells):
        cls, text = cells[i]
        field = RUC_LABEL_MAPPING.get(_normalize_ruc_label(text))
        if cls != "bgn" or not field:
            i += 1
            continue
        values = []
        j = i + 1
        while j < len(cells):
            ncls, ntxt = cells[j]
            nfield = RUC_LABEL_MAPPING.get(_normalize_ruc_label(ntxt))
            if ncls == "bgn" and nfield:
                break
            if ncls == "bg" and ntxt:
                values.append(ntxt)
            j += 1
        if values:
            vals[field] = "\n".join(values)
        i = j
    return vals


def _extract_ruc_h4_tokens(raw_html: str) -> Dict[str, str]:
    body = re.sub(r"(?is)<script.*?</script>", " ", raw_html or "")
    body = re.sub(r"(?is)<style.*?</style>", " ", body)
    tokens = [
        (tag.lower(), _clean_ruc_text(content))
        for tag, content in re.findall(r"(?is)<(h4|p|td)\b[^>]*>(.*?)</\1>", body)
        if _clean_ruc_text(content)
    ]
    vals = {}
    i = 0
    while i < len(tokens):
        tag, text = tokens[i]
        field = RUC_LABEL_MAPPING.get(_normalize_ruc_label(text))
        if tag != "h4" or not field:
            i += 1
            continue
        ni = i + 1
        value = ""
        if ni < len(tokens) and tokens[ni][0] in ("h4", "p"):
            value = tokens[ni][1]
            i = ni + 1
        elif ni < len(tokens) and tokens[ni][0] == "td":
            td_vals = []
            while ni < len(tokens) and tokens[ni][0] == "td":
                td_vals.append(tokens[ni][1])
                ni += 1
            value = "\n".join(td_vals)
            i = ni
        else:
            i += 1
        if value:
            vals[field] = value
    return vals


def _parse_ruc_html(raw_html: str) -> Dict[str, str]:
    vals = _extract_ruc_legacy_table(raw_html)
    vals.update(_extract_ruc_h4_tokens(raw_html))
    numero_ruc = vals.get("numero_ruc")
    if numero_ruc:
        match = re.match(r"^\s*(\d{11})\s*-\s*(.+?)\s*$", numero_ruc)
        if match:
            vals["ruc"] = match.group(1)
            vals["razon_social"] = match.group(2)
    if not vals.get("ruc") or not vals.get("razon_social"):
        raise ValueError("No se pudo extraer RUC y razón social desde la respuesta de SUNAT.")
    return vals


class ConsultaDocumentoService:
    """
    Servicio de consulta externa resiliente de documentos de identidad en Perú.
    - DNI (8 dígitos): Consulta oficial RENIEC (vía API ciudadana pública).
    - RUC (11 dígitos): Consulta SUNAT en tiempo real para personas jurídicas / naturales con negocio.
    """

    @classmethod
    def consultar_dni(cls, dni: str) -> Dict[str, Any]:
        """
        Consulta DNI de 8 dígitos y devuelve el nombre exacto del portador/titular.
        """
        dni_limpio = re.sub(r"\D", "", dni or "")
        if len(dni_limpio) != 8:
            return {
                "success": False,
                "found": False,
                "tipo_documento": "dni",
                "error": "El DNI debe contener exactamente 8 dígitos numéricos."
            }

        url = RENIEC_DNI_URL.format(dni=dni_limpio)
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(url)

            if response.status_code != 200:
                logger.warning(f"RENIEC API retornó HTTP {response.status_code} para DNI {dni_limpio}")
                return {
                    "success": False,
                    "found": False,
                    "tipo_documento": "dni",
                    "error": f"RENIEC respondió código HTTP {response.status_code}."
                }

            data = response.json()
            if not isinstance(data, dict):
                return {"success": False, "found": False, "tipo_documento": "dni", "error": "Formato de respuesta no reconocido."}

            nombres = (data.get("nombres") or "").strip()
            apellido_paterno = (data.get("apellido_paterno") or "").strip()
            apellido_materno = (data.get("apellido_materno") or "").strip()

            partes = [nombres, apellido_paterno, apellido_materno]
            nombre_completo = " ".join(p for p in partes if p).strip()

            if not nombre_completo:
                return {
                    "success": False,
                    "found": False,
                    "tipo_documento": "dni",
                    "error": "No se encontraron nombres asociados a este DNI."
                }

            return {
                "success": True,
                "found": True,
                "source": "reniec",
                "tipo_documento": "dni",
                "tipo_cliente": "persona_natural",
                "numero_documento": dni_limpio,
                "nombre_completo": nombre_completo,
                "nombres": nombres,
                "apellido_paterno": apellido_paterno,
                "apellido_materno": apellido_materno,
                "fecha_nacimiento": data.get("fecha_nacimiento", ""),
                "sexo": data.get("sexo", "")
            }

        except httpx.TimeoutException:
            logger.warning(f"Timeout al consultar RENIEC para DNI {dni_limpio}")
            return {
                "success": False,
                "found": False,
                "tipo_documento": "dni",
                "error": "Tiempo de espera agotado al consultar RENIEC. Puedes ingresar el nombre manualmente."
            }
        except Exception as exc:
            logger.error(f"Error inesperado al consultar RENIEC: {exc}")
            return {
                "success": False,
                "found": False,
                "tipo_documento": "dni",
                "error": "Servicio de consulta no disponible temporalmente. Completa los datos manualmente."
            }

    @classmethod
    def consultar_ruc(cls, ruc: str) -> Dict[str, Any]:
        """
        Consulta RUC de 11 dígitos ante SUNAT en tiempo real y parsea la razón social oficial.
        """
        ruc_limpio = re.sub(r"\D", "", ruc or "")
        if len(ruc_limpio) != 11:
            return {
                "success": False,
                "found": False,
                "tipo_documento": "ruc",
                "error": "El RUC debe contener exactamente 11 dígitos numéricos."
            }

        payload = {
            "accion": "consPorRuc",
            "nroRuc": ruc_limpio,
            "token": "x",
            "contexto": "ti-it",
            "modo": "1"
        }

        try:
            import requests
            response = requests.post(SUNAT_RUC_URL, headers=SUNAT_HEADERS, data=payload, timeout=8.0)

            if response.status_code != 200:
                logger.warning(f"SUNAT respondió código HTTP {response.status_code} para RUC {ruc_limpio}")
                return {
                    "success": False,
                    "found": False,
                    "tipo_documento": "ruc",
                    "error": f"SUNAT respondió código HTTP {response.status_code}."
                }

            parsed_data = _parse_ruc_html(response.text)
            razon_social = parsed_data.get("razon_social", "").strip()

            return {
                "success": True,
                "found": True,
                "source": "sunat",
                "tipo_documento": "ruc",
                "tipo_cliente": "empresa",
                "numero_documento": parsed_data.get("ruc", ruc_limpio),
                "nombre_completo": razon_social,
                "razon_social": razon_social,
                "nombre_comercial": parsed_data.get("nombre_comercial", ""),
                "estado_contribuyente": parsed_data.get("estado_contribuyente", ""),
                "condicion_contribuyente": parsed_data.get("condicion_contribuyente", ""),
                "domicilio_fiscal": parsed_data.get("domicilio_fiscal", "")
            }

        except Exception as exc:
            logger.warning(f"No se pudo consultar SUNAT RUC: {exc}")
            return {
                "success": False,
                "found": False,
                "tipo_documento": "ruc",
                "error": "SUNAT no devolvió datos para este RUC o requiere validación manual."
            }

    @classmethod
    def consultar_documento(cls, documento: str, tipo_hint: Optional[str] = None) -> Dict[str, Any]:
        """
        Punto de entrada unificado para consulta de documentos peruanos.
        Detecta automáticamente DNI (8 dígitos) o RUC (11 dígitos).
        """
        doc_limpio = re.sub(r"\D", "", documento or "").strip()
        tipo = (tipo_hint or "").lower().strip()

        if len(doc_limpio) == 8 or tipo == "dni":
            return cls.consultar_dni(doc_limpio)
        elif len(doc_limpio) == 11 or tipo == "ruc":
            return cls.consultar_ruc(doc_limpio)
        else:
            return {
                "success": False,
                "found": False,
                "tipo_documento": tipo or "desconocido",
                "error": "El documento debe tener 8 dígitos (DNI) o 11 dígitos (RUC)."
            }
