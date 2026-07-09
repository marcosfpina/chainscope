# services/collector/adapters/rate_limited_mixin.py

"""
RateLimitedMixin — injeta AdaptiveRateLimiter + CircuitBreaker em qualquer adapter.

Todos os adapters Tier 1-4 herdam este mixin para garantir que requests
respeitem rate limits e falhas em cascata sejam contidas.

Uso:
    class MyAdapter(RateLimitedMixin, BaseAdapter):
        def __init__(self):
            self.__init_rate_limiter__(initial_delay_ms=300.0)
            ...

        async def collect(self, params):
            await self._acquire()
            result = await self._call_protected(self._do_request, url)
            await self._report(result.status_code, result.elapsed_ms)
            ...
"""

import time
from typing import Any, Callable

from spider_nix import AdaptiveRateLimiter, CircuitBreaker, CircuitBreakerConfig, CircuitBreakerError


class RateLimitedMixin:
    """
    Mixin de rate limiting e circuit breaking para adapters do CHAINSCOPE.

    Deve ser inicializado via __init_rate_limiter__() no __init__ do adapter.
    Usar _acquire() antes de cada request e _report() após receber a resposta.
    """

    def __init_rate_limiter__(
        self,
        initial_delay_ms: float = 500.0,
        min_delay_ms: float = 100.0,
        max_delay_ms: float = 5000.0,
        failure_threshold: int = 5,
        timeout_seconds: float = 60.0,
    ) -> None:
        """
        Inicializa rate limiter e circuit breaker.

        Args:
            initial_delay_ms: Delay inicial entre requests (ms).
            min_delay_ms: Delay mínimo adaptativo (ms).
            max_delay_ms: Delay máximo — aplicado em backpressure severo (ms).
            failure_threshold: Falhas consecutivas para abrir o circuit breaker.
            timeout_seconds: Segundos em aberto antes de tentar half-open.
        """
        self._rate_limiter = AdaptiveRateLimiter(
            initial_delay_ms=initial_delay_ms,
            min_delay_ms=min_delay_ms,
            max_delay_ms=max_delay_ms,
        )
        self._circuit_breaker = CircuitBreaker(
            config=CircuitBreakerConfig(
                failure_threshold=failure_threshold,
                timeout_seconds=timeout_seconds,
            )
        )

    async def _acquire(self) -> None:
        """Aguarda o delay adaptativo antes de fazer o próximo request."""
        if not hasattr(self, "_rate_limiter"):
            raise RuntimeError(
                f"{type(self).__name__}: chame __init_rate_limiter__() no __init__"
            )
        await self._rate_limiter.acquire()

    async def _report(self, status_code: int, elapsed_ms: float) -> None:
        """
        Reporta o resultado de um request para ajuste adaptativo do rate limiter.

        Args:
            status_code: Código HTTP da resposta (ex: 200, 429, 503).
            elapsed_ms: Tempo de resposta em milissegundos.
        """
        error = status_code >= 500
        await self._rate_limiter.report_request(
            status_code=status_code,
            response_time_ms=elapsed_ms,
            error=error,
        )

    async def _call_protected(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """
        Executa func com proteção do circuit breaker.

        Raises:
            CircuitBreakerError: quando o circuito está aberto (falhas em cascata).
        """
        if not hasattr(self, "_circuit_breaker"):
            raise RuntimeError(
                f"{type(self).__name__}: chame __init_rate_limiter__() no __init__"
            )
        return await self._circuit_breaker.call(func, *args, **kwargs)

    def get_rate_limit_stats(self) -> dict:
        """Retorna estatísticas atuais do rate limiter (para observabilidade)."""
        if not hasattr(self, "_rate_limiter"):
            return {}
        stats = self._rate_limiter.get_stats()
        return {
            "current_delay_ms": stats.current_delay_ms,
            "circuit_state": self._circuit_breaker.get_state().value
            if hasattr(self, "_circuit_breaker")
            else "unknown",
        }
