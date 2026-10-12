# Kimss Python SDK — LLM / IDE context

Pair with [AI_INTEGRATION.md](../AI_INTEGRATION.md), [README.md](../README.md), and [KIMSS_ONBOARDING.md](KIMSS_ONBOARDING.md).

## Clean machine checklist (do this first)

0. **Kimss app (human or operator):** Provider Vault (`/app/vault`) — register each `custom:<model_id>`. Gateway API key (`/app/keys`).
1. **Python ≥ 3.10** available.
2. For **inference**: keep the native SDK already in the repo — `pip install openai` and/or `pip install anthropic`. Point it at the Kimss gateway (no Kimss SDK required).
3. Optional control-plane package: `pip install kimss` (register agents, report usage). Declared dep: `requests>=2.28`.
4. Set env: `KIMSS_API_KEY` (alias `KIMSS_WORKSPACE_KEY`), `KIMSS_AGENT_ID`. OpenAI default host `https://api.kimss.ai/v1`. Anthropic default host `https://api.kimss.ai`.
5. **Preferred first call:** official OpenAI client → `POST /v1/chat/completions` **or** official Anthropic client → `POST /v1/messages`, always with `X-Kimss-Agent-Id`.
6. **Agents Discovery:** inventory rows appear JIT after first gateway traffic. Endpoint governance (monthly token caps, Article 12 assurance) lives in Provider Vault — not as agent checkboxes.
7. **Deprecated:** `KimssClient.agents.run`, `chat`, `Agent.query`, `models.create`, MCP `kimss_chat` / `kimss_run_agent` / `kimss_complete`.

## Preferred inference (dual-listener gateway)

**OpenAI** (`base_url=https://api.kimss.ai/v1`):

```python
import os
from openai import OpenAI

client = OpenAI(
    base_url=os.getenv("KIMSS_GATEWAY_URL", "https://api.kimss.ai/v1"),
    api_key=os.getenv("KIMSS_API_KEY") or os.getenv("KIMSS_WORKSPACE_KEY"),
)
resp = client.chat.completions.create(
    model=os.getenv("KIMSS_MODEL", "custom:your-vaulted-model"),
    messages=[{"role": "user", "content": "Hello"}],
    extra_headers={
        "X-Kimss-Agent-Id": os.getenv("KIMSS_AGENT_ID", "my_agent"),
        "X-Kimss-Agent-Name": os.getenv("KIMSS_AGENT_NAME", "My Agent"),
    },
)
```

**Anthropic** (`base_url=https://api.kimss.ai` — the SDK appends `/v1/messages`):

```python
import os
from anthropic import Anthropic

client = Anthropic(
    base_url=os.getenv("ANTHROPIC_BASE_URL", "https://api.kimss.ai"),
    api_key=os.getenv("KIMSS_API_KEY") or os.getenv("KIMSS_WORKSPACE_KEY"),
)
resp = client.messages.create(
    model=os.getenv("KIMSS_MODEL", "custom:your-vaulted-model"),
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello"}],
    extra_headers={
        "X-Kimss-Agent-Id": os.getenv("KIMSS_AGENT_ID", "my_agent"),
        "X-Kimss-Agent-Name": os.getenv("KIMSS_AGENT_NAME", "My Agent"),
    },
)
```

Auth: `Authorization: Bearer kimss_...`, `X-Kimss-Key`, or Anthropic-style `x-api-key`.

## Control plane (DevOps) — `kimss` package

| Concern | How |
|---------|-----|
| Register external agent | `client.agents.register(...)` → `POST /v1/agents/register` |
| Report BYO usage | `client.usage.report(...)` → `POST /v1/usage/events` |
| Vault BYO endpoint + optional token cap | REST `POST/PATCH /api/v1/custom-model-endpoints` or Provider Vault UI (`/app/vault`) |
| Kill switch | Governance UI or `POST /agent_set_status/` `{id, status: "disabled"\|"active"}` (admin) |
| Article 12–style audit | Gateway → Recent calls; `POST /audit_log/` for tenant admin events; APIM GatewayLogs when enabled |
| MCP sync | Provider Vault (UI); do not invent a public MCP HTTP proxy URL |

Native auth for control-plane calls: **`X-Kimss-Key`**. Base URL for `KimssClient`: `https://api.kimss.ai` (no `/v1` suffix).

## Deprecated SDK method → HTTP map

| SDK surface (deprecated for inference) | HTTP |
|----------------------------------------|------|
| `KimssClient.chat` / `Agent.query` / `agents.run` | `POST /v1/agents/run` |
| `KimssClient.models.create` | `POST /v1/models/completions` |
| `KimssClient.images.generate` | `POST /v1/images/generations` |

Still valid management: `agents.create`, `agents.register`, `usage.report`, `files.upload`, `add_function_to_agent`.

## Dual-listener base URLs

```text
OpenAI:    base_url = https://api.kimss.ai/v1
Anthropic: base_url = https://api.kimss.ai
api_key    = kimss_...
headers    = X-Kimss-Agent-Id, X-Kimss-Agent-Name
```

Do **not** point Azure official clients at Kimss inbound URLs. Vault Azure and call through the OpenAI or Anthropic listener.

## Error code dictionary

| HTTP | `detail.error` | Meaning |
|------|----------------|---------|
| 403 | `agent_disabled` | Kill switch — stop; re-enable in Governance |
| 403 | `subscription_required` | Upgrade / switch workspace |
| 429 | `governed_requests_exhausted` | Monthly free allowance hit |
| 429 | `credit_pool_exhausted` / trial / policy | Stop; surface to user |
| 429 | `rate_limit_exceeded` | Backoff / Retry-After |

## MCP tools (stdio) — optional IDE

Install: `pip install 'kimss[mcp]'`. Inference tools (`kimss_chat`, `kimss_run_agent`, `kimss_complete`) are **deprecated**; prefer the OpenAI or Anthropic gateway from app code. Management tools remain for create/upload/function attach.
