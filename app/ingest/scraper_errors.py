# app/ingest/scraper_errors.py
"""
Manejo de errores para el scraper de Flashscore
Define excepciones personalizadas y funciones de logging
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger("betdesk.scraper")


# ============================================================================
# EXCEPCIONES PERSONALIZADAS
# ============================================================================

class ScraperError(Exception):
    """Excepción base para errores del scraper"""
    
    def __init__(self, message: str, context: Dict[str, Any] = None):
        super().__init__(message)
        self.message = message
        self.context = context or {}
        self.timestamp = datetime.now(timezone.utc)
    
    def __str__(self):
        return f"{self.__class__.__name__}: {self.message}"


class RateLimitError(ScraperError):
    """Error cuando se excede el rate limit"""
    pass


class ParsingError(ScraperError):
    """Error al parsear HTML"""
    pass


class EventNotFoundError(ScraperError):
    """Error cuando no se encuentra un evento"""
    pass


class InvalidHTMLError(ScraperError):
    """Error cuando el HTML es inválido o incompleto"""
    pass


class NetworkError(ScraperError):
    """Error de red/conexión"""
    pass


class AuthenticationError(ScraperError):
    """Error de autenticación (si Flashscore requiere login)"""
    pass


class DataValidationError(ScraperError):
    """Error al validar datos scrapeados"""
    pass


# ============================================================================
# LOGGING DE ERRORES
# ============================================================================

def log_scraper_error(
    error: Exception,
    context: Dict[str, Any] = None,
    level: str = "error"
):
    """
    Log detallado de errores del scraper
    
    Args:
        error: Excepción capturada
        context: Contexto adicional (URL, deporte, etc.)
        level: Nivel de logging ("error", "warning", "info")
    """
    context = context or {}
    
    error_info = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **context
    }
    
    # Formatear mensaje
    msg = f"Scraper error: {error_info['error_type']} - {error_info['error_message']}"
    
    if context:
        msg += f" | Context: {context}"
    
    # Log según nivel
    if level == "error":
        logger.error(msg)
    elif level == "warning":
        logger.warning(msg)
    else:
        logger.info(msg)
    
    # Si es ScraperError personalizado, log contexto adicional
    if isinstance(error, ScraperError) and error.context:
        logger.debug(f"Additional context: {error.context}")


def log_parsing_failure(
    html_snippet: str,
    expected_element: str,
    url: str = None
):
    """
    Log específico para fallos de parsing
    
    Args:
        html_snippet: Fragmento de HTML que falló
        expected_element: Elemento que se esperaba encontrar
        url: URL del evento (opcional)
    """
    context = {
        "expected": expected_element,
        "html_length": len(html_snippet),
        "url": url
    }
    
    logger.warning(
        f"Parsing failed: Could not find '{expected_element}' | "
        f"HTML length: {len(html_snippet)} | URL: {url}"
    )
    
    # Log snippet de HTML para debugging (solo primeros 200 chars)
    if len(html_snippet) > 0:
        snippet = html_snippet[:200].replace('\n', ' ')
        logger.debug(f"HTML snippet: {snippet}...")


def log_rate_limit_hit(delay: float, url: str = None):
    """
    Log cuando se alcanza el rate limit
    
    Args:
        delay: Tiempo de espera en segundos
        url: URL afectada (opcional)
    """
    logger.warning(
        f"⏱️  Rate limit hit. Waiting {delay:.1f}s before retry | URL: {url}"
    )


def log_retry_attempt(
    attempt: int,
    max_attempts: int,
    error: Exception,
    url: str = None
):
    """
    Log de intentos de retry
    
    Args:
        attempt: Número de intento actual
        max_attempts: Máximo de intentos
        error: Error que causó el retry
        url: URL afectada (opcional)
    """
    logger.info(
        f"🔄 Retry attempt {attempt}/{max_attempts} after {type(error).__name__} | "
        f"URL: {url}"
    )


# ============================================================================
# VALIDACIÓN DE DATOS
# ============================================================================

def validate_scraped_data(data: Dict[str, Any], data_type: str) -> bool:
    """
    Valida datos scrapeados
    
    Args:
        data: Datos a validar
        data_type: Tipo de datos ("event", "odds")
        
    Returns:
        True si es válido
        
    Raises:
        DataValidationError: Si los datos son inválidos
    """
    if data_type == "event":
        return _validate_event_data(data)
    elif data_type == "odds":
        return _validate_odds_data(data)
    else:
        raise ValueError(f"Unknown data type: {data_type}")


def _validate_event_data(event: Dict[str, Any]) -> bool:
    """Valida datos de un evento"""
    required_fields = ["sport", "league", "home", "away", "start_time_utc", "flashscore_url"]
    
    for field in required_fields:
        if field not in event:
            raise DataValidationError(
                f"Missing required field: {field}",
                context={"event": event}
            )
        
        if event[field] is None or event[field] == "":
            raise DataValidationError(
                f"Empty required field: {field}",
                context={"event": event}
            )
    
    # Validar tipos
    if not isinstance(event["start_time_utc"], datetime):
        raise DataValidationError(
            "start_time_utc must be datetime",
            context={"event": event}
        )
    
    # Validar valores
    valid_sports = ["basketball", "football", "tennis"]
    if event["sport"] not in valid_sports:
        raise DataValidationError(
            f"Invalid sport: {event['sport']}. Must be one of {valid_sports}",
            context={"event": event}
        )
    
    return True


def _validate_odds_data(odds: Dict[str, Any]) -> bool:
    """Valida datos de una odd"""
    required_fields = ["market", "bookmaker", "selection", "odds", "captured_at_utc"]
    
    for field in required_fields:
        if field not in odds:
            raise DataValidationError(
                f"Missing required field: {field}",
                context={"odds": odds}
            )
    
    # Validar odds value
    if not isinstance(odds["odds"], (int, float)):
        raise DataValidationError(
            "odds must be numeric",
            context={"odds": odds}
        )
    
    if odds["odds"] < 1.01 or odds["odds"] > 1000:
        raise DataValidationError(
            f"odds value out of range: {odds['odds']}",
            context={"odds": odds}
        )
    
    # Validar line si existe
    if odds.get("line") is not None:
        if not isinstance(odds["line"], (int, float)):
            raise DataValidationError(
                "line must be numeric",
                context={"odds": odds}
            )
    
    return True


# ============================================================================
# MANEJO DE ERRORES HTTP
# ============================================================================

def handle_http_error(response, url: str = None):
    """
    Maneja errores HTTP de requests
    
    Args:
        response: requests.Response object
        url: URL de la request (opcional)
        
    Raises:
        NetworkError: Para errores de red
        RateLimitError: Para rate limiting (429)
        AuthenticationError: Para errores de auth (401, 403)
        ScraperError: Para otros errores
    """
    status_code = response.status_code
    
    if status_code == 429:
        raise RateLimitError(
            "Rate limit exceeded",
            context={"url": url, "status_code": status_code}
        )
    
    elif status_code in (401, 403):
        raise AuthenticationError(
            f"Authentication failed: {status_code}",
            context={"url": url, "status_code": status_code}
        )
    
    elif status_code == 404:
        raise EventNotFoundError(
            "Event not found (404)",
            context={"url": url}
        )
    
    elif status_code >= 500:
        raise NetworkError(
            f"Server error: {status_code}",
            context={"url": url, "status_code": status_code}
        )
    
    elif status_code >= 400:
        raise ScraperError(
            f"HTTP error: {status_code}",
            context={"url": url, "status_code": status_code}
        )


# ============================================================================
# ESTADÍSTICAS DE ERRORES
# ============================================================================

class ErrorStats:
    """Clase para trackear estadísticas de errores"""
    
    def __init__(self):
        self.total_errors = 0
        self.errors_by_type = {}
        self.errors_by_url = {}
        self.last_error_time = None
    
    def record_error(self, error: Exception, url: str = None):
        """Registra un error"""
        self.total_errors += 1
        self.last_error_time = datetime.now(timezone.utc)
        
        # Por tipo
        error_type = type(error).__name__
        self.errors_by_type[error_type] = self.errors_by_type.get(error_type, 0) + 1
        
        # Por URL
        if url:
            self.errors_by_url[url] = self.errors_by_url.get(url, 0) + 1
    
    def get_error_rate(self, total_requests: int) -> float:
        """Calcula tasa de error"""
        if total_requests == 0:
            return 0.0
        return (self.total_errors / total_requests) * 100
    
    def get_most_common_error(self) -> Optional[str]:
        """Retorna el tipo de error más común"""
        if not self.errors_by_type:
            return None
        return max(self.errors_by_type, key=self.errors_by_type.get)
    
    def get_problematic_urls(self, threshold: int = 3) -> list:
        """Retorna URLs con más errores que el umbral"""
        return [
            url for url, count in self.errors_by_url.items()
            if count >= threshold
        ]
    
    def reset(self):
        """Resetea estadísticas"""
        self.total_errors = 0
        self.errors_by_type = {}
        self.errors_by_url = {}
        self.last_error_time = None
    
    def __str__(self):
        return (
            f"ErrorStats(total={self.total_errors}, "
            f"types={len(self.errors_by_type)}, "
            f"urls={len(self.errors_by_url)})"
        )


# Instancia global de estadísticas
error_stats = ErrorStats()


# ============================================================================
# UTILIDADES
# ============================================================================

def should_retry_error(error: Exception) -> bool:
    """
    Determina si un error debería ser reintentado
    
    Args:
        error: Excepción a evaluar
        
    Returns:
        True si debería reintentarse
    """
    # Reintentar errores de red
    if isinstance(error, NetworkError):
        return True
    
    # Reintentar rate limits (con delay)
    if isinstance(error, RateLimitError):
        return True
    
    # NO reintentar errores de parsing (probablemente estructura cambió)
    if isinstance(error, ParsingError):
        return False
    
    # NO reintentar errores de validación
    if isinstance(error, DataValidationError):
        return False
    
    # NO reintentar eventos no encontrados
    if isinstance(error, EventNotFoundError):
        return False
    
    # Por defecto, reintentar
    return True


def get_retry_delay(error: Exception, attempt: int) -> float:
    """
    Calcula delay para retry basado en el tipo de error
    
    Args:
        error: Excepción que causó el retry
        attempt: Número de intento
        
    Returns:
        Delay en segundos
    """
    base_delay = 5.0
    
    # Rate limit: delay más largo
    if isinstance(error, RateLimitError):
        return base_delay * (2 ** attempt) * 2  # Backoff más agresivo
    
    # Network error: backoff exponencial normal
    if isinstance(error, NetworkError):
        return base_delay * (2 ** attempt)
    
    # Otros errores: delay fijo
    return base_delay
