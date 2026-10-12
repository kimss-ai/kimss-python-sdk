#!/usr/bin/env python3
"""Invisible Proxy with automatic Run-Id / lineage (setup-once, non-Forge).

Env:
  KIMSS_API_KEY or KIMSS_WORKSPACE_KEY
  KIMSS_AGENT_ID (root / orchestrator)
  KIMSS_MODEL
  KIMSS_GATEWAY_URL (optional)

Toggle Observe/Enforce in Guardrails — keep this client in place.
"""
from __future__ import annotations

import os
import sys

from kimss.proxy import KimssProxy


def main() -> None:
    key = (os.environ.get("KIMSS_API_KEY") or os.environ.get("KIMSS_WORKSPACE_KEY") or "").strip()
    agent_id = (os.environ.get("KIMSS_AGENT_ID") or "orchestrator").strip()
    model = (os.environ.get("KIMSS_MODEL") or "").strip()
    if not key or not model:
        print("Set KIMSS_API_KEY (or KIMSS_WORKSPACE_KEY) and KIMSS_MODEL.", file=sys.stderr)
        raise SystemExit(1)

    proxy = KimssProxy(api_key=key, agent_id=agent_id, agent_name="Orchestrator")
    # Prefer OpenAI SDK when installed; else requests path.
    try:
        client = proxy.openai()
        r = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Plan a one-step research handoff."}],
        )
        print(r.choices[0].message.content)
    except ImportError:
        data = proxy.chat_completions(
            model=model,
            messages=[{"role": "user", "content": "Plan a one-step research handoff."}],
        )
        print(data["choices"][0]["message"]["content"])

    ctx = proxy.current_context()
    print("run_id (Swarm Runs):", ctx.run_id if ctx else None)
    if proxy.pending_child:
        print("pending child depth:", proxy.pending_child.depth)
        # Child hop example (same process):
        # proxy.delegate(agent_id="researcher")
        # client.chat.completions.create(...)


if __name__ == "__main__":
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass
    main()
