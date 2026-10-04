# Getting started with the Kimss Secure AI Gateway

**Track, govern, and secure autonomous agents with exactly 1 line of code.**

Kimss is the **Secure AI Gateway** and **Governance Control Plane**: identity, audit, kill switch, and a provider vault. You bring the models (**BYOI**).

**Start with a 14-day Production trial (no card):** 100,000 governed requests/month during the trial · [Sign up](https://kimss.ai/app/signup)

## Step 1 — Sign In & Vault

Open **Governance → Provider Vault** / Connected Infrastructure (`/app/governance/custom-models`). Add your OpenAI, Azure OpenAI / Foundry, Anthropic, DeepSeek, or vLLM endpoint. The key is vaulted and never returned to clients. On paid plans you can optionally set a **monthly token cap** per endpoint (alert or block) — separate from governed requests. See [Connected Infrastructure docs](https://kimss.ai/docs/custom_model_endpoints).

## Step 2 — Mint a Control-Plane key

Open **Gateway** → **Generate Key**. Copy the `kimss_...` secret once. Same keys under **Governance → API Keys**.

## Step 3 — Route traffic (zero refactoring)

### OpenAI client

```python
import os
from openai import OpenAI

client = OpenAI(
    base_url=os.getenv("KIMSS_GATEWAY_URL", "https://api.kimss.ai/v1"),
    api_key=os.getenv("KIMSS_WORKSPACE_KEY") or os.getenv("KIMSS_API_KEY"),
)
response = client.chat.completions.create(
    model=os.getenv("KIMSS_MODEL", "custom:your-vaulted-model"),
    messages=[{"role": "user", "content": "Hello via Kimss Gateway"}],
    extra_headers={
        "X-Kimss-Agent-Id": os.getenv("KIMSS_AGENT_ID", "my_agent"),
        "X-Kimss-Agent-Name": os.getenv("KIMSS_AGENT_NAME", "My Agent"),
    },
)
```

### Anthropic client

```python
import os
from anthropic import Anthropic

client = Anthropic(
    base_url=os.getenv("ANTHROPIC_BASE_URL", "https://api.kimss.ai"),
    api_key=os.getenv("KIMSS_WORKSPACE_KEY") or os.getenv("KIMSS_API_KEY"),
)
response = client.messages.create(
    model=os.getenv("KIMSS_MODEL", "custom:your-vaulted-model"),
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello via Kimss Gateway"}],
    extra_headers={
        "X-Kimss-Agent-Id": os.getenv("KIMSS_AGENT_ID", "my_agent"),
        "X-Kimss-Agent-Name": os.getenv("KIMSS_AGENT_NAME", "My Agent"),
    },
)
```

The Anthropic SDK appends `/v1/messages`. Do not set `base_url` to `https://api.kimss.ai/v1`.

### Zero-code `.env`

```bash
OPENAI_BASE_URL="https://api.kimss.ai/v1"
OPENAI_API_KEY="kimss_your_kimss_key"
# or
ANTHROPIC_BASE_URL="https://api.kimss.ai"
ANTHROPIC_API_KEY="kimss_your_kimss_key"
```

Azure official clients are **not** inbound drop-ins. Vault Azure (and any other backend) under Provider Vault, then call Kimss with the OpenAI or Anthropic client above.

## Step 4 — Monitor and kill switch

- **Gateway → Recent calls** — attributed to your `X-Kimss-Agent-Id` (or JIT-discovered).
- **Governance → Agents** — disable an agent → HTTP **403** `agent_disabled`.

## Control plane (optional)

`pip install kimss` for `agents.register` and `usage.report`. Kill switch / audit / MCP sync: Governance UI or REST (`POST /agent_set_status/`, `POST /audit_log/`). Do not use `KimssClient` for chat/completions/messages.

## Related

- [AI_INTEGRATION.md](AI_INTEGRATION.md) — mandatory rules for AI coding assistants
- [README.md](README.md)
- [docs/llm-context.md](docs/llm-context.md)
