#!/usr/bin/env python3
"""Canonical Kimss gateway proxy — official OpenAI client + X-Kimss-Agent-Id headers.

Env:
  KIMSS_API_KEY or KIMSS_WORKSPACE_KEY (required)
  KIMSS_AGENT_ID (required for attribution / kill switch)
  KIMSS_MODEL (required — vaulted logical id, e.g. custom:...)
  KIMSS_GATEWAY_URL (optional, default https://api.kimss.ai/v1)
  KIMSS_AGENT_NAME (optional)
"""
from __future__ import annotations

import os
import sys

from openai import OpenAI

from kimss.gateway_headers import gateway_headers


def main() -> None:
    key = (os.environ.get("KIMSS_API_KEY") or os.environ.get("KIMSS_WORKSPACE_KEY") or "").strip()
    agent_id = (os.environ.get("KIMSS_AGENT_ID") or "").strip()
    model = (os.environ.get("KIMSS_MODEL") or "").strip()
    if not key or not agent_id or not model:
        print(
            "Set KIMSS_API_KEY (or KIMSS_WORKSPACE_KEY), KIMSS_AGENT_ID, and KIMSS_MODEL.",
            file=sys.stderr,
        )
        raise SystemExit(1)
    base = (os.environ.get("KIMSS_GATEWAY_URL") or "https://api.kimss.ai/v1").rstrip("/")
    name = (os.environ.get("KIMSS_AGENT_NAME") or "Gateway Proxy Agent").strip()

    client = OpenAI(base_url=base, api_key=key)
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "Execute database audit."}],
        extra_headers=gateway_headers(agent_id=agent_id, agent_name=name),
    )
    print(resp.choices[0].message.content)


if __name__ == "__main__":
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass
    main()
