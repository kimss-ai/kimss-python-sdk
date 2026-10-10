"""Kimss Python SDK – integration layer for the Kimss Secure AI Gateway."""
from .gateway_headers import gateway_headers
from .client import Agent, AgentRunResult, AgentRunUsage, KimssClient
from .environment import KimssEnv, current_env, env_label, is_staging, redis_cache_namespace_infix
from .errors import (
    KimssApiError,
    KimssCreditExhausted,
    KimssGovernedRequestsExhausted,
    KimssRateLimited,
    KimssSubscriptionRequired,
    raise_for_kimss_error,
)
from .privacy import BeforeRequestHook, PresidioRedactor
from .proxy import KimssProxy
from .run_context import (
    RunContext,
    clear_run_contexts,
    ensure_root_context,
    get_pending_child,
    get_run_context,
)

__all__ = [
    "KimssClient",
    "KimssProxy",
    "RunContext",
    "ensure_root_context",
    "get_run_context",
    "get_pending_child",
    "clear_run_contexts",
    "gateway_headers",
    "Agent",
    "AgentRunResult",
    "AgentRunUsage",
    "KimssEnv",
    "current_env",
    "env_label",
    "is_staging",
    "redis_cache_namespace_infix",
    "KimssApiError",
    "KimssCreditExhausted",
    "KimssGovernedRequestsExhausted",
    "KimssSubscriptionRequired",
    "KimssRateLimited",
    "raise_for_kimss_error",
    "BeforeRequestHook",
    "PresidioRedactor",
]
