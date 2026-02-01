# app/ingest/scraper_config.py
"""
Configuración del scraper para Flashscore
Incluye rate limiting, user agents y manejo de errores
"""

import time
import random
import logging
from typing import Dict, Callable, Any
from functools import wraps

logger = logging.getLogger("betdesk.scraper")

# ============================================================================
# CONFIGURACIÓN DEL SCRAPER
# ============================================================================

SCRAPER_CONFIG = {
    # Rate limiting
    "delay_between_requests": 2.0,  # segundos entre requests
    "delay_variance": 1.0,  # variación aleatoria (+/- segundos)
    
    # Timeouts
    "timeout": 30,  # segundos
    "connect_timeout": 10,
    
    # Reintentos
    "max_retries": 3,
    "retry_delay": 5,  # segundos
    "retry_backoff": 2,  # multiplicador exponencial
    
    # Headers
    "rotate_user_agents": True,
    "use_random_headers": True,
}

# ============================================================================
# USER AGENTS
# ============================================================================

USER_AGENTS = [
    # Chrome on Windows
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    
    # Chrome on Mac
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    
    # Firefox on Windows
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
    
    # Firefox on Mac
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
    
    # Safari on Mac
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    
    # Edge on Windows
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
]

# ============================================================================
# HEADERS
# ============================================================================

def get_headers() -> Dict[str, str]:
    """
    Retorna headers HTTP para requests
    Rota user agent si está configurado
    """
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0',
    }
    
    # Agregar user agent
    if SCRAPER_CONFIG["rotate_user_agents"]:
        headers['User-Agent'] = get_random_user_agent()
    else:
        headers['User-Agent'] = USER_AGENTS[0]
    
    # Agregar headers aleatorios adicionales
    if SCRAPER_CONFIG["use_random_headers"]:
        if random.random() > 0.5:
            headers['Referer'] = 'https://www.google.com/'
    
    return headers


def get_random_user_agent() -> str:
    """Retorna un user agent aleatorio de la lista"""
    return random.choice(USER_AGENTS)


# ============================================================================
# RATE LIMITING
# ============================================================================

_last_request_time = 0.0

def apply_rate_limit():
    """
    Aplica rate limiting entre requests
    Espera el tiempo configurado desde el último request
    """
    global _last_request_time
    
    current_time = time.time()
    time_since_last = current_time - _last_request_time
    
    delay = SCRAPER_CONFIG["delay_between_requests"]
    variance = SCRAPER_CONFIG["delay_variance"]
    
    # Agregar variación aleatoria
    actual_delay = delay + random.uniform(-variance, variance)
    actual_delay = max(0.5, actual_delay)  # Mínimo 0.5 segundos
    
    if time_since_last < actual_delay:
        sleep_time = actual_delay - time_since_last
        logger.debug(f"⏱️  Rate limiting: sleeping {sleep_time:.2f}s")
        time.sleep(sleep_time)
    
    _last_request_time = time.time()


def reset_rate_limit():
    """Resetea el contador de rate limiting"""
    global _last_request_time
    _last_request_time = 0.0


# ============================================================================
# RETRY DECORATOR
# ============================================================================

def retry_on_failure(max_retries: int = None, delay: float = None, backoff: float = None):
    """
    Decorator para reintentar funciones que fallan
    
    Args:
        max_retries: Número máximo de reintentos (default: config)
        delay: Delay inicial entre reintentos (default: config)
        backoff: Multiplicador exponencial (default: config)
    
    Usage:
        @retry_on_failure(max_retries=3)
        def my_function():
            ...
    """
    if max_retries is None:
        max_retries = SCRAPER_CONFIG["max_retries"]
    if delay is None:
        delay = SCRAPER_CONFIG["retry_delay"]
    if backoff is None:
        backoff = SCRAPER_CONFIG["retry_backoff"]
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        logger.warning(
                            f"⚠️  {func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}): {e}"
                        )
                        logger.info(f"Retrying in {current_delay:.1f}s...")
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"❌ {func.__name__} failed after {max_retries + 1} attempts"
                        )
            
            # Si llegamos aquí, todos los intentos fallaron
            raise last_exception
        
        return wrapper
    return decorator


# ============================================================================
# CIRCUIT BREAKER
# ============================================================================

class CircuitBreaker:
    """
    Circuit breaker para detener scraping si hay muchos errores
    
    Estados:
    - CLOSED: Funcionando normalmente
    - OPEN: Demasiados errores, bloqueando requests
    - HALF_OPEN: Probando si el servicio se recuperó
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Ejecuta función con circuit breaker"""
        
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
                logger.info("🔄 Circuit breaker: HALF_OPEN (testing recovery)")
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self):
        """Llamado cuando una operación tiene éxito"""
        self.failure_count = 0
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
            logger.info("✅ Circuit breaker: CLOSED (recovered)")
    
    def _on_failure(self):
        """Llamado cuando una operación falla"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.error(
                f"🚫 Circuit breaker: OPEN (too many failures: {self.failure_count})"
            )
    
    def _should_attempt_reset(self) -> bool:
        """Verifica si es tiempo de intentar recuperación"""
        if self.last_failure_time is None:
            return True
        
        return (time.time() - self.last_failure_time) >= self.recovery_timeout
    
    def reset(self):
        """Resetea el circuit breaker manualmente"""
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"
        logger.info("🔄 Circuit breaker: RESET")


# ============================================================================
# INSTANCIA GLOBAL DE CIRCUIT BREAKER
# ============================================================================

# Circuit breaker para scraping de Flashscore
flashscore_circuit_breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=300.0,  # 5 minutos
    expected_exception=Exception
)


# ============================================================================
# UTILIDADES
# ============================================================================

def log_request(url: str, status_code: int = None, error: str = None):
    """Log de requests para debugging"""
    if error:
        logger.error(f"❌ Request failed: {url} - {error}")
    elif status_code:
        if 200 <= status_code < 300:
            logger.debug(f"✅ Request OK: {url} [{status_code}]")
        else:
            logger.warning(f"⚠️  Request warning: {url} [{status_code}]")
    else:
        logger.debug(f"📡 Request: {url}")


def validate_response(response) -> bool:
    """
    Valida que una respuesta HTTP sea válida
    
    Args:
        response: requests.Response object
        
    Returns:
        bool: True si es válida
    """
    if response.status_code != 200:
        return False
    
    if len(response.content) < 1000:  # Muy pequeño, probablemente error
        return False
    
    # Verificar que no sea una página de error
    if b'error' in response.content.lower()[:500]:
        return False
    
    return True


# ============================================================================
# CONFIGURACIÓN DE LOGGING
# ============================================================================

def setup_scraper_logging(level: str = "INFO"):
    """
    Configura logging para el scraper
    
    Args:
        level: Nivel de logging ("DEBUG", "INFO", "WARNING", "ERROR")
    """
    logging.basicConfig(
        level=getattr(logging, level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    logger.setLevel(getattr(logging, level))
