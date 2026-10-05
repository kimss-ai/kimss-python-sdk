"""Helpers for OpenAI/Anthropic gateway clients (canonical integration path)."""
from __future__ import annotations

from typing import Dict, Optional

from .telemetry.context import encode_sdk_context_header_value


def gateway_headers(
    *,
    agent_id: str,
    agent_name: Optional[str] = None,
    resource_type: str = "agent",
    env: Optional[str] = None,
    region: Optional[str] = None,
    hostname: Optional[str] = None,
    run_id: Optional[str] = None,
    depth: Optional[int] = None,
    parent_span: Optional[str] = None,
    span_id: Optional[str] = None,
    lineage: Optional[str] = None,
) -> Dict[str, str]:
    """
    Return ``extra_headers`` for official OpenAI/Anthropic SDK clients pointed at Kimss.

    Includes agent attribution plus optional ``X-Kimss-SDK-Context`` for named call sites in Agent Tracking.
    """
    aid = (agent_id or "").strip()
    if not aid:
        raise ValueError("agent_id is required")
    headers: Dict[str, str] = {"X-Kimss-Agent-Id": aid}
    name = (agent_name or "").strip()
    if name:
        headers["X-Kimss-Agent-Name"] = name
    try:
        headers["X-Kimss-SDK-Context"] = encode_sdk_context_header_value(
            resource_type=resource_type,
            resource_name=aid,
            env=env,
            region=region,
            hostname=hostname,
        )
    except Exception:
        pass
    if (run_id or "").strip():
        headers["X-Kimss-Run-Id"] = str(run_id).strip()
    if depth is not None:
        headers["X-Kimss-Depth"] = str(int(depth))
    if (parent_span or "").strip():
        headers["X-Kimss-Parent-Span"] = str(parent_span).strip()
    if (span_id or "").strip():
        headers["X-Kimss-Span-Id"] = str(span_id).strip()
    if (lineage or "").strip():
        headers["X-Kimss-Lineage"] = str(lineage).strip()
    return headers
