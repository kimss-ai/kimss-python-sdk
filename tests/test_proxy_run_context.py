"""Unit tests for Invisible Proxy auto RunContext (no live gateway)."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from kimss.proxy import KimssProxy
from kimss.run_context import (
    absorb_response_lineage,
    advance_to_pending_child,
    clear_run_contexts,
    ensure_root_context,
    get_pending_child,
    get_run_context,
    lineage_headers_from_mapping,
    run_context_from_lineage_headers,
)


@pytest.fixture(autouse=True)
def _clean_ctx():
    clear_run_contexts()
    yield
    clear_run_contexts()


def test_ensure_root_mints_run_id():
    ctx = ensure_root_context()
    assert ctx.run_id
    assert ctx.depth == 0
    assert ctx.span_id
    assert get_run_context() is ctx
    # idempotent
    assert ensure_root_context().run_id == ctx.run_id


def test_lineage_headers_case_insensitive():
    lin = lineage_headers_from_mapping(
        {
            "x-kimss-run-id": "r1",
            "X-Kimss-Depth": "1",
            "x-kimss-parent-span": "p",
            "X-Kimss-Span-Id": "c",
            "x-kimss-lineage": "tok",
        }
    )
    assert lin["X-Kimss-Run-Id"] == "r1"
    assert lin["X-Kimss-Depth"] == "1"
    ctx = run_context_from_lineage_headers(lin)
    assert ctx is not None
    assert ctx.run_id == "r1"
    assert ctx.depth == 1
    assert ctx.parent_span == "p"
    assert ctx.span_id == "c"
    assert ctx.lineage == "tok"


def test_absorb_then_advance_child():
    ensure_root_context()
    absorb_response_lineage(
        {
            "X-Kimss-Run-Id": "runabc",
            "X-Kimss-Depth": "1",
            "X-Kimss-Parent-Span": "rootspan",
            "X-Kimss-Span-Id": "childspan",
            "X-Kimss-Lineage": "hmac-token",
        }
    )
    pending = get_pending_child()
    assert pending is not None
    assert pending.depth == 1
    child = advance_to_pending_child()
    assert get_run_context() is child
    assert child.span_id == "childspan"
    assert get_pending_child() is None


def test_advance_without_pending_raises():
    ensure_root_context()
    with pytest.raises(RuntimeError, match="No pending child"):
        advance_to_pending_child()


def test_proxy_request_headers_include_agent_and_run():
    proxy = KimssProxy(api_key="kimss_test", agent_id="orchestrator", agent_name="Orch")
    headers = proxy.request_headers()
    assert headers["X-Kimss-Agent-Id"] == "orchestrator"
    assert headers["X-Kimss-Agent-Name"] == "Orch"
    assert headers["X-Kimss-Run-Id"]
    assert headers["X-Kimss-Depth"] == "0"
    assert headers["X-Kimss-Span-Id"]


def test_proxy_delegate_uses_pending_and_switches_agent():
    proxy = KimssProxy(api_key="k", agent_id="orch")
    proxy.request_headers()  # mint root
    proxy.absorb_response_headers(
        {
            "X-Kimss-Run-Id": "r9",
            "X-Kimss-Depth": "1",
            "X-Kimss-Parent-Span": "s0",
            "X-Kimss-Span-Id": "s1",
            "X-Kimss-Lineage": "sig",
        }
    )
    ctx = proxy.delegate(agent_id="researcher")
    assert proxy.agent_id == "researcher"
    assert ctx.depth == 1
    assert ctx.span_id == "s1"
    hdrs = proxy.request_headers()
    assert hdrs["X-Kimss-Agent-Id"] == "researcher"
    assert hdrs["X-Kimss-Run-Id"] == "r9"
    assert hdrs["X-Kimss-Depth"] == "1"
    assert hdrs["X-Kimss-Lineage"] == "sig"


@patch("kimss.proxy.requests.post")
def test_chat_completions_sends_lineage_and_absorbs_response(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": "ok"}}],
    }
    mock_resp.headers = {
        "X-Kimss-Run-Id": "run1",
        "X-Kimss-Depth": "1",
        "X-Kimss-Parent-Span": "parent1",
        "X-Kimss-Span-Id": "child1",
        "X-Kimss-Lineage": "token1",
    }
    mock_resp.text = "{}"
    mock_post.return_value = mock_resp

    proxy = KimssProxy(api_key="kimss_k", agent_id="orch")
    data = proxy.chat_completions(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": "hi"}],
    )
    assert data["choices"][0]["message"]["content"] == "ok"
    assert data["_kimss_lineage"]["X-Kimss-Span-Id"] == "child1"

    sent_headers = mock_post.call_args.kwargs["headers"]
    assert sent_headers["X-Kimss-Agent-Id"] == "orch"
    assert sent_headers["X-Kimss-Run-Id"]
    assert sent_headers["Authorization"] == "Bearer kimss_k"

    proxy.delegate(agent_id="child-agent")
    assert proxy.agent_id == "child-agent"
    assert get_run_context() is not None
    assert get_run_context().span_id == "child1"


def test_openai_wrapper_injects_headers_and_absorbs_raw_response():
    proxy = KimssProxy(api_key="k", agent_id="orch")

    class FakeRaw:
        headers = {
            "X-Kimss-Run-Id": "rz",
            "X-Kimss-Depth": "1",
            "X-Kimss-Parent-Span": "a",
            "X-Kimss-Span-Id": "b",
            "X-Kimss-Lineage": "t",
        }

        def parse(self):
            return {"ok": True}

    class FakeCompletions:
        def __init__(self):
            self.last_kwargs = None
            self.with_raw_response = self

        def create(self, **kwargs):
            self.last_kwargs = kwargs
            return FakeRaw()

    comps = FakeCompletions()

    class FakeChat:
        def __init__(self):
            self.completions = comps

    class FakeOpenAI:
        def __init__(self):
            self.chat = FakeChat()

    from kimss.proxy import _OpenAIProxy

    client = _OpenAIProxy(FakeOpenAI(), proxy)
    out = client.chat.completions.create(model="m", messages=[])
    assert out == {"ok": True}
    assert comps.last_kwargs["extra_headers"]["X-Kimss-Agent-Id"] == "orch"
    assert comps.last_kwargs["extra_headers"]["X-Kimss-Run-Id"]
    assert proxy.pending_child is not None
    assert proxy.pending_child.span_id == "b"
