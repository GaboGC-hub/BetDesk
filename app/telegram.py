#app/telegram.py
import os
import logging
import requests
from dotenv import load_dotenv
from typing import Optional, Dict
import time

load_dotenv()

logger = logging.getLogger("betdesk.telegram")


# ============================================================================
# ENVÍO BÁSICO A TELEGRAM
# ============================================================================

def send_telegram(text: str, retry: int = 3) -> bool:
    """
    Envía mensaje a Telegram (HTML).
    """
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        logger.warning("⚠️ Telegram no configurado")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    for attempt in range(retry):
        try:
            r = requests.post(
                url,
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True,
                },
                timeout=15,
            )
            r.raise_for_status()
            logger.info("✅ Error de cuota enviado a Telegram")
            return True

        except requests.exceptions.Timeout:
            logger.warning(f"⏱️ Timeout Telegram ({attempt+1}/{retry})")
            time.sleep(2 ** attempt)

        except requests.exceptions.HTTPError as e:
            logger.error(f"❌ Telegram HTTP error: {e.response.text}")
            if e.response.status_code == 429:
                time.sleep(int(e.response.headers.get("Retry-After", 5)))
            else:
                break

        except Exception as e:
            logger.error(f"❌ Telegram error: {e}")
            time.sleep(2 ** attempt)

    return False


# ============================================================================
# FORMATO FIJO DEL MENSAJE (NO TOCAR)
# ============================================================================

def format_error_cuota_message(
    odd: Dict,
    error_detection: Dict
) -> str:
    """
    ⚠️ FORMATO FIJO — NO MODIFICAR
    """

    return "\n".join([
        "📊 ERROR DE CUOTA - BALONCESTO",
        f"🏆 {odd.get('league', '')}",
        f"🏀 {odd.get('event', '')}",
        f"🕐 {odd.get('start_time', '')}",
        f"📊 Mercado: {odd.get('market', '')}",
        f"🎲 {odd.get('selection', '')} {odd.get('line', '')} @ {odd.get('odds', '')}",
        f"🏪 {odd.get('bookmaker', '')}",
        f"📈 Z-score: {error_detection.get('deviation_sigmas', 0):.2f}",
    ])


# ============================================================================
# FILTRO ESTRICTO — SOLO ERRORES DE CUOTA REALES
# ============================================================================

def maybe_send_error_cuota_to_telegram(
    odd: Dict,
    error_detection: Dict
) -> bool:
    """
    Envía a Telegram SOLO si:
    - Es error real
    - Error humano
    - A favor nuestro
    - Acción: BET_IMMEDIATELY
    """

    if not error_detection:
        return False

    # 1️⃣ Debe ser error
    if not error_detection.get("is_error"):
        return False

    # 2️⃣ SOLO errores humanos
    if error_detection.get("error_type") != "HUMAN_ERROR":
        return False

    # 3️⃣ Solo si la cuota es MEJOR que la esperada
    actual_odd = error_detection.get("actual_odd")
    expected_odd = error_detection.get("expected_odd")

    if actual_odd is None or expected_odd is None:
        return False

    if actual_odd <= expected_odd:
        return False

    # 4️⃣ Debe ser apostar YA
    if error_detection.get("action") != "BET_IMMEDIATELY":
        return False

    # 5️⃣ Confianza mínima dura
    if error_detection.get("confidence", 0) < 0.75:
        return False

    # ✅ PASÓ TODOS LOS FILTROS
    message = format_error_cuota_message(odd, error_detection)
    return send_telegram(message)
