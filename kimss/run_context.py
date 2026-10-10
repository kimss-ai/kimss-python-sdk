"""Declared-run context for Invisible Proxy clients (OpenAI / Anthropic).

Mirrors Forge lineage semantics without requiring ``kimss-forge``.
Gateway response headers mint the *next* child hop; call ``take_pending_child``
(or ``KimssProxy.delegate``) before the child agent's request.
"""
from __future__ import annotations

import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field, replace
from typing import Any, Dict, Mapping, Optional

LINEAGE_HEADER_KEYS = (
    "X-Kimss-Run-Id",
    "X-Kimss-Depth",
    "X-Kimss-Parent-Span",
    "X-Kimss-Span-Id",
    "X-Kimss-Lineage",
)


@dataclass
class RunContext:
    """Lineage carried across proxy hops."""

    run_id: str
    depth: int = 0
    parent_span: Optional[str] = None
    span_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    lineage: Optional[str] = None

    def headers(self) -> Dict[str, str]:
        out: Dict[str, str] = {
            "X-Kimss-Run-Id": self.run_id,
            "X-Kimss-Depth": str(int(self.depth)),
            "X-Kimss-Span-Id": self.span_id,
        }
        if self.parent_span:
            out["X-Kimss-Parent-Span"] = self.parent_span
        if self.lineage:
            out["X-Kimss-Lineage"] = self.lineage
        return out


_CURRENT: ContextVar[Optional[RunContext]] = ContextVar("kimss_sdk_run_context", default=None)
_PENDING_CHILD: ContextVar[Optional[RunContext]] = ContextVar(
    "kimss_sdk_pending_child", default=None
)


def get_run_context() -> Optional[RunContext]:
    return _CURRENT.get()


def set_run_context(ctx: Optional[RunContext]) -> None:
    _CURRENT.set(ctx)


def ensure_root_context() -> RunContext:
    cur = _CURRENT.get()
    if cur is not None:
        return cur
    ctx = RunContext(run_id=uuid.uuid4().hex, depth=0, span_id=uuid.uuid4().hex[:16])
    _CURRENT.set(ctx)
    return ctx


def get_pending_child() -> Optional[RunContext]:
    return _PENDING_CHILD.get()


def set_pending_child(ctx: Optional[RunContext]) -> None:
    _PENDING_CHILD.set(ctx)


def take_pending_child() -> Optional[RunContext]:
    pending = _PENDING_CHILD.get()
    _PENDING_CHILD.set(None)
    return pending


def clear_run_contexts() -> None:
    """Reset contextvars (tests / new top-level run)."""
    _CURRENT.set(None)
    _PENDING_CHILD.set(None)


def run_context_from_lineage_headers(lin: Mapping[str, Any]) -> Optional[RunContext]:
    if not isinstance(lin, Mapping) or not lin:
        return None
    # Case-insensitive lookup
    lower = {str(k).lower(): v for k, v in lin.items()}
    token = lower.get("x-kimss-lineage")
    run_id = lower.get("x-kimss-run-id")
    depth_raw = lower.get("x-kimss-depth")
    parent = lower.get("x-kimss-parent-span")
    span = lower.get("x-kimss-span-id")
    if not run_id or span is None or depth_raw is None:
        return None
    try:
        depth = int(depth_raw)
    except (TypeError, ValueError):
        return None
    return RunContext(
        run_id=str(run_id),
        depth=depth,
        parent_span=str(parent) if parent else None,
        span_id=str(span),
        lineage=str(token) if token else None,
    )


def lineage_headers_from_mapping(headers: Mapping[str, Any]) -> Dict[str, str]:
    """Extract Kimss lineage headers from an HTTP header map (any casing)."""
    if not isinstance(headers, Mapping):
        return {}
    lower = {str(k).lower(): v for k, v in headers.items()}
    out: Dict[str, str] = {}
    for key in LINEAGE_HEADER_KEYS:
        val = lower.get(key.lower())
        if val is not None and str(val).strip():
            out[key] = str(val).strip()
    return out


def absorb_response_lineage(headers: Mapping[str, Any]) -> Optional[RunContext]:
    """Store server-minted *next-hop* identity from response headers."""
    lin = lineage_headers_from_mapping(headers)
    pending = run_context_from_lineage_headers(lin)
    if pending is not None:
        set_pending_child(pending)
    return pending


def advance_to_pending_child() -> RunContext:
    """Promote pending child to current context (child agent hop)."""
    pending = take_pending_child()
    if pending is None:
        raise RuntimeError(
            "No pending child lineage. Call the parent hop first so the gateway "
            "can mint X-Kimss-Lineage on the response."
        )
    set_run_context(pending)
    return pending
