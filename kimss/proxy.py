"""Invisible Proxy client with automatic declared-run lineage.

Setup-once for non-Forge customers::

    from kimss.proxy import KimssProxy

    proxy = KimssProxy(api_key="kimss_...", agent_id="orchestrator")
    client = proxy.openai()  # OpenAI SDK pointed at Kimss
    client.chat.completions.create(...)  # mints/sends Run-Id + lineage

    proxy.delegate(agent_id="researcher")  # advance to child hop
    client.chat.completions.create(...)

Toggle Observe/Enforce in Guardrails — keep this client; no redeploy to turn off.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, Mapping, Optional

import requests

from .gateway_headers import gateway_headers
from .run_context import (
    RunContext,
    absorb_response_lineage,
    advance_to_pending_child,
    clear_run_contexts,
    ensure_root_context,
    get_pending_child,
    get_run_context,
    lineage_headers_from_mapping,
    set_run_context,
)

DEFAULT_OPENAI_GATEWAY = "https://api.kimss.ai/v1"
DEFAULT_ANTHROPIC_GATEWAY = "https://api.kimss.ai"


class KimssProxy:
    """Holds agent identity + run lineage for OpenAI/Anthropic-through-Kimss."""

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        agent_id: str,
        agent_name: Optional[str] = None,
        openai_base_url: Optional[str] = None,
        anthropic_base_url: Optional[str] = None,
        timeout: float = 120.0,
        auto_root: bool = True,
    ) -> None:
        aid = (agent_id or "").strip()
        if not aid:
            raise ValueError("agent_id is required")
        self.api_key = (
            api_key
            or os.environ.get("KIMSS_WORKSPACE_KEY")
            or os.environ.get("KIMSS_API_KEY")
            or ""
        ).strip()
        self.agent_id = aid
        self.agent_name = (agent_name or "").strip() or None
        self.openai_base_url = (
            openai_base_url
            or os.environ.get("KIMSS_GATEWAY_URL")
            or DEFAULT_OPENAI_GATEWAY
        ).rstrip("/")
        anth = (
            anthropic_base_url
            or os.environ.get("ANTHROPIC_BASE_URL")
            or os.environ.get("KIMSS_BASE_URL")
            or DEFAULT_ANTHROPIC_GATEWAY
        ).rstrip("/")
        if anth.endswith("/v1"):
            anth = anth[: -len("/v1")]
        self.anthropic_base_url = anth
        self.timeout = timeout
        self.auto_root = bool(auto_root)
        self.pending_child: Optional[RunContext] = None

    def reset_run(self) -> RunContext:
        """Start a new root run (clears current + pending)."""
        clear_run_contexts()
        self.pending_child = None
        return ensure_root_context()

    def current_context(self) -> Optional[RunContext]:
        return get_run_context()

    def request_headers(self, extra: Optional[Mapping[str, str]] = None) -> Dict[str, str]:
        """Agent + lineage headers for the next gateway hop."""
        if self.auto_root:
            ensure_root_context()
        ctx = get_run_context()
        kwargs: Dict[str, Any] = {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
        }
        if ctx is not None:
            kwargs.update(
                run_id=ctx.run_id,
                depth=ctx.depth,
                parent_span=ctx.parent_span,
                span_id=ctx.span_id,
                lineage=ctx.lineage,
            )
        headers = gateway_headers(**kwargs)
        if extra:
            headers.update({str(k): str(v) for k, v in extra.items() if v is not None})
        return headers

    def absorb_response_headers(self, headers: Mapping[str, Any]) -> Optional[RunContext]:
        pending = absorb_response_lineage(headers)
        self.pending_child = pending
        return pending

    def delegate(self, *, agent_id: str, agent_name: Optional[str] = None) -> RunContext:
        """Advance to the gateway-minted child hop and switch agent attribution."""
        aid = (agent_id or "").strip()
        if not aid:
            raise ValueError("agent_id is required for delegate")
        # Prefer instance stash (set by openai/anthropic wrappers), else contextvar.
        if self.pending_child is not None:
            ctx = self.pending_child
            self.pending_child = None
            from .run_context import take_pending_child

            take_pending_child()  # clear twin
            set_run_context(ctx)
        else:
            ctx = advance_to_pending_child()
        self.agent_id = aid
        if agent_name is not None:
            self.agent_name = (agent_name or "").strip() or None
        return ctx

    def openai(self, **client_kwargs: Any) -> Any:
        """Return an ``openai.OpenAI`` client with auto lineage on chat.completions.create."""
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ImportError(
                "openai package required for KimssProxy.openai(). pip install openai"
            ) from exc
        if not self.api_key:
            raise ValueError("api_key required (or set KIMSS_API_KEY / KIMSS_WORKSPACE_KEY)")
        kwargs = dict(client_kwargs)
        kwargs.setdefault("base_url", self.openai_base_url)
        kwargs.setdefault("api_key", self.api_key)
        client = OpenAI(**kwargs)
        return _OpenAIProxy(client, self)

    def anthropic(self, **client_kwargs: Any) -> Any:
        """Return an ``anthropic.Anthropic`` client with auto lineage on messages.create."""
        try:
            from anthropic import Anthropic
        except ImportError as exc:
            raise ImportError(
                "anthropic package required for KimssProxy.anthropic(). pip install anthropic"
            ) from exc
        if not self.api_key:
            raise ValueError("api_key required (or set KIMSS_API_KEY / KIMSS_WORKSPACE_KEY)")
        kwargs = dict(client_kwargs)
        kwargs.setdefault("base_url", self.anthropic_base_url)
        kwargs.setdefault("api_key", self.api_key)
        client = Anthropic(**kwargs)
        return _AnthropicProxy(client, self)

    def chat_completions(
        self,
        *,
        model: str,
        messages: list,
        tools: Optional[list] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Requests-based chat completions (no openai package). Absorbs lineage headers."""
        if not self.api_key:
            raise ValueError("api_key required (or set KIMSS_API_KEY / KIMSS_WORKSPACE_KEY)")
        url = f"{self.openai_base_url}/chat/completions"
        payload: Dict[str, Any] = {"model": model, "messages": messages}
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if temperature is not None:
            payload["temperature"] = temperature
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            **self.request_headers(extra_headers),
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
        if resp.status_code >= 400:
            raise RuntimeError(f"chat completions failed ({resp.status_code}): {resp.text[:400]}")
        try:
            data = resp.json()
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"invalid JSON ({resp.status_code}): {resp.text[:400]}") from exc
        pending = self.absorb_response_headers(resp.headers)
        lin = lineage_headers_from_mapping(resp.headers)
        if lin:
            data["_kimss_lineage"] = lin
        elif pending is not None:
            data["_kimss_lineage"] = pending.headers()
        return data


class _OpenAIProxy:
    """Thin attribute proxy; wraps chat.completions.create for lineage."""

    def __init__(self, client: Any, proxy: KimssProxy) -> None:
        self._client = client
        self._proxy = proxy

    def __getattr__(self, name: str) -> Any:
        if name == "chat":
            return _ChatProxy(self._client.chat, self._proxy)
        return getattr(self._client, name)


class _ChatProxy:
    def __init__(self, chat: Any, proxy: KimssProxy) -> None:
        self._chat = chat
        self._proxy = proxy

    def __getattr__(self, name: str) -> Any:
        if name == "completions":
            return _CompletionsProxy(self._chat.completions, self._proxy)
        return getattr(self._chat, name)


class _CompletionsProxy:
    def __init__(self, completions: Any, proxy: KimssProxy) -> None:
        self._completions = completions
        self._proxy = proxy

    def __getattr__(self, name: str) -> Any:
        return getattr(self._completions, name)

    def create(self, *args: Any, **kwargs: Any) -> Any:
        extra = dict(kwargs.pop("extra_headers", None) or {})
        kwargs["extra_headers"] = self._proxy.request_headers(extra)
        raw_factory = getattr(self._completions, "with_raw_response", None)
        if raw_factory is not None:
            raw = raw_factory.create(*args, **kwargs)
            headers = getattr(raw, "headers", None) or {}
            self._proxy.absorb_response_headers(headers)
            return raw.parse()
        return self._completions.create(*args, **kwargs)


class _AnthropicProxy:
    def __init__(self, client: Any, proxy: KimssProxy) -> None:
        self._client = client
        self._proxy = proxy

    def __getattr__(self, name: str) -> Any:
        if name == "messages":
            return _MessagesProxy(self._client.messages, self._proxy)
        return getattr(self._client, name)


class _MessagesProxy:
    def __init__(self, messages: Any, proxy: KimssProxy) -> None:
        self._messages = messages
        self._proxy = proxy

    def __getattr__(self, name: str) -> Any:
        return getattr(self._messages, name)

    def create(self, *args: Any, **kwargs: Any) -> Any:
        extra = dict(kwargs.pop("extra_headers", None) or {})
        kwargs["extra_headers"] = self._proxy.request_headers(extra)
        raw_factory = getattr(self._messages, "with_raw_response", None)
        if raw_factory is not None:
            raw = raw_factory.create(*args, **kwargs)
            headers = getattr(raw, "headers", None) or {}
            self._proxy.absorb_response_headers(headers)
            return raw.parse()
        return self._messages.create(*args, **kwargs)


__all__ = [
    "KimssProxy",
    "DEFAULT_OPENAI_GATEWAY",
    "DEFAULT_ANTHROPIC_GATEWAY",
    "get_run_context",
    "get_pending_child",
    "ensure_root_context",
    "clear_run_contexts",
]
