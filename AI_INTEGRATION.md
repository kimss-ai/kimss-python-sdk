# AI Integration — Kimss Gateway (Agent-to-Agent)

> **Canonical public A2A contract (always fetch this URL when onboarding a customer app):**  
> https://raw.githubusercontent.com/kimss-ai/kimss-control-plane/main/AI_INTEGRATION.md  
> ([kimss-ai/kimss-control-plane](https://github.com/kimss-ai/kimss-control-plane))  
> This file is a mirror for local SDK / quickstart assistants. Prefer the raw GitHub URL above.
# AI Integration ג€” Kimss Control Plane (Agent-to-Agent)

**Canonical public A2A contract** for Cursor, Cascade, Claude Code, Windsurf, Devin, and other coding assistants.

**Fetch URL (always prefer this over cloning):**

```text
https://raw.githubusercontent.com/kimss-ai/kimss-control-plane/main/AI_INTEGRATION.md
```

Kimss is a **Model-Agnostic Enterprise AI Gateway and Governance Control Plane** with a **dual-listener** inbound proxy:

| Listener | Method | URL |
|----------|--------|-----|
| OpenAI syntax | `POST` | `https://api.kimss.ai/v1/chat/completions` |
| Anthropic syntax | `POST` | `https://api.kimss.ai/v1/messages` |

Runtime SSOT remains `kimssApi`. This repo is the **public contract hub** ג€” **do not clone** control-plane source into the customer app. Rewire the **customer** codebase only.

Product companion: https://kimss.ai/docs/route_traffic

---

## Cascade / coding-agent procedure (follow in order)

When the user asks you to onboard a repo to Kimss (or ג€route traffic through the Kimss gatewayג€):

1. **Confirm prerequisites** (user should already have done these in the Kimss UI). If not, stop and tell them to complete:
   - Provider Vault (`/app/vault`) ג€” each model they call must exist as `custom:<model_id>`
   - Gateway API key (`/app/keys`) ג€” a `kimss_...` workspace key (not the provider key)
2. **Detect** whether the codebase uses OpenAI-compatible clients, Anthropic clients, or both (SDK imports, `OPENAI_*` / `ANTHROPIC_*` env, LangChain/Vercel AI `baseURL`, raw `fetch` to `api.openai.com` / `api.anthropic.com`).
3. **Keep the native client** ג€” never introduce `KimssClient` for chat/completions/messages.
4. **Point the client at Kimss:**
   - OpenAI-compatible ג†’ `base_url` / `baseURL` = `https://api.kimss.ai/v1`
   - Anthropic ג†’ `base_url` / `baseURL` = `https://api.kimss.ai` (**no** `/v1/messages` suffix ג€” the SDK appends it)
5. **Swap the API key** to the Gateway `kimss_...` key via env (`OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `KIMSS_API_KEY`). Never commit provider keys.
6. **Map models** to vaulted aliases (`custom:your-model-id`). Do not leave bare `gpt-4o` / `claude-ג€¦` unless that exact string is what was vaulted.
7. **Always send** `X-Kimss-Agent-Id` (and preferably `X-Kimss-Agent-Name`) on inference ג€” via `default_headers`, `defaultHeaders`, `extra_headers`, or middleware. Pick a stable slug per service (e.g. `billing-bot`).
8. **Forward headers** through any HTTP interceptor / proxy / Hermis-style middleware ג€” never strip Kimss agent headers.
9. **Verify** (see [Verification](#verification-after-wiring) below). Do not claim success until a live call works or the user confirms Vault + key + model alias.

Optional: `pip install kimss` only if you want `kimss.gateway_headers(...)` for Agent Tracking context ג€” **not** required for inference.

---

## Prerequisites (Kimss app ג€” before repo changes)

1. **Provider Vault** (`/app/vault`): register each `custom:<model_id>` you will call. One vault row per model alias; you may reuse the same provider API key across models.
2. **Gateway API key** (`/app/keys`): mint a `kimss_...` workspace key.
3. **Route traffic** in the app: base URL + Gateway key + agent headers (this file).

If a model is not vaulted, Kimss returns an error pointing to Provider Vault. **Agents** (`/app/agents`) populate automatically after the first governed request that includes `X-Kimss-Agent-Id` ג€” you do **not** need to create agents in the UI first.

---

## Rules (do not violate)

1. **Never** use a custom `KimssClient` for chat/completions/messages or any LLM inference.
2. **Keep** the codebaseג€™s native OpenAI or Anthropic SDK (or OpenAI-compatible HTTP client) ג€” zero data-plane refactoring.
3. **OpenAI:** `base_url` = `https://api.kimss.ai/v1`.
4. **Anthropic:** `base_url` = `https://api.kimss.ai` only.
5. **Always** inject `X-Kimss-Agent-Id` (preferably also `X-Kimss-Agent-Name`) for JIT inventory, audit, spend attribution, and kill-switch. Omitting it may still proxy, but agents appear as unattributed / model-labelled shadow rows and kill-switch by name is weaker.
6. **Call-site visibility (recommended):** when `kimss` is installed, use `kimss.gateway_headers(agent_id=..., agent_name=...)` as `extra_headers`. A plain dict with `X-Kimss-Agent-Id` is enough.
7. **Streaming** works the same (`stream=True` / `stream: true`) ג€” keep Kimss base URL and headers.
8. **Control-plane API** (registry, MCP RBAC, audit, metering, kill switch): use [`openapi/control-plane.yaml`](openapi/control-plane.yaml) ג€” not chat endpoints. OpenAPI does **not** duplicate inference paths; this file is the inference contract.
9. **Hermis** is the Kimss orchestration framework (not LangGraph). The gateway applies identity, kill switch, spend policy, and audit on the routed hop.

---

## Environment variables (zero / minimal code)

```bash
# OpenAI-compatible clients
OPENAI_BASE_URL="https://api.kimss.ai/v1"
OPENAI_API_KEY="kimss_your_gateway_key"

# Anthropic clients
ANTHROPIC_BASE_URL="https://api.kimss.ai"
ANTHROPIC_API_KEY="kimss_your_gateway_key"

# Recommended for header injection in app config
KIMSS_AGENT_ID="my-service"
KIMSS_AGENT_NAME="My Service"
KIMSS_MODEL="custom:your-model-id"
```

You still must attach `X-Kimss-Agent-Id` in code or middleware ג€” env alone does not add headers for most SDKs.

---

## OpenAI (Python)

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://api.kimss.ai/v1",  # required
    api_key="kimss_workspace_key",  # Gateway key ג€” not the provider key
    default_headers={
        "X-Kimss-Agent-Id": "my-service",
        "X-Kimss-Agent-Name": "My Service",
    },
)
response = client.chat.completions.create(
    model="custom:your-model-id",  # vaulted alias
    messages=[{"role": "user", "content": "Execute audit."}],
)
```

## OpenAI (Node / TypeScript)

```typescript
import OpenAI from "openai";

const client = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY, // kimss_...
  baseURL: "https://api.kimss.ai/v1",
  defaultHeaders: {
    "X-Kimss-Agent-Id": process.env.KIMSS_AGENT_ID ?? "my-service",
    "X-Kimss-Agent-Name": process.env.KIMSS_AGENT_NAME ?? "My Service",
  },
});

const response = await client.chat.completions.create({
  model: process.env.KIMSS_MODEL ?? "custom:your-model-id",
  messages: [{ role: "user", content: "Execute audit." }],
});
```

## Anthropic (Python)

```python
from anthropic import Anthropic

client = Anthropic(
    base_url="https://api.kimss.ai",
    api_key="kimss_workspace_key",
    default_headers={
        "X-Kimss-Agent-Id": "my-service",
        "X-Kimss-Agent-Name": "My Service",
    },
)
response = client.messages.create(
    model="custom:your-model-id",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Execute audit."}],
)
```

Full Anthropic env-var path and troubleshooting: [docs/anthropic-onboarding.md](docs/anthropic-onboarding.md).

Auth also accepts `X-Kimss-Key` and Anthropic-style `x-api-key` with a `kimss_...` workspace key.

### Frameworks (LangChain, Vercel AI SDK, etc.)

Same contract: set the provider **base URL** to the Kimss listener above, use the Gateway key, and ensure every outbound LLM HTTP call includes `X-Kimss-Agent-Id`. Prefer one middleware / `defaultHeaders` so tool loops cannot drop attribution.

---

## Verification (after wiring)

1. Make one non-stream chat/completions or messages call with the vaulted `custom:ג€¦` model.
2. Expect **200** and a normal assistant payload (not HTML login pages).
3. In Kimss UI: **Agents** (`/app/agents`) shows the `X-Kimss-Agent-Id` after the first call.
4. Optional meter check:

```bash
curl -s -H "Authorization: Bearer kimss_..." \
  https://api.kimss.ai/api/v1/governed-requests/meter
```

Shape: [`examples/governed-requests-meter-response.json`](examples/governed-requests-meter-response.json).

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `401` / invalid API key | Wrong or missing `kimss_...` key | Mint under **Gateway ג†’ Keys** (`/app/keys`) |
| `400` / missing agent / attribution errors | Header stripped or empty where required by a path | Set `X-Kimss-Agent-Id` on every inference call |
| `403` / `agent_disabled` | Kill switch | Re-enable under **Governance ג†’ Agents** |
| `429` / `governed_requests_exhausted` | Monthly allowance | Check meter or [pricing](https://kimss.ai/pricing) |
| `429` / `custom_endpoint_cap_exceeded` | Vault token cap | Raise/disable cap on the vaulted endpoint |
| Model not found / vault error | Model not registered as `custom:ג€¦` | Vault under `/app/vault`; match the exact model string |
| Anthropic path errors | `base_url` includes `/v1/messages` | Use `https://api.kimss.ai` only |
| OpenAI 404 on `/chat/completions` | Used Anthropic base without `/v1` | OpenAI must use `https://api.kimss.ai/v1` |

---

## What `KimssClient` is for

Control-plane / DevOps only (`agents.register`, `usage.report`). Inference methods are deprecated. Prefer this file + native SDKs for chat.

## Kill switch

HTTP **403** with `agent_disabled` (OpenAI `error.code` or Anthropic error body).

## Control-plane quick path

| Task | Endpoint | Doc |
|------|----------|-----|
| Check monthly cap | `GET /api/v1/governed-requests/meter` | OpenAPI |
| Register MCP server | `POST /api/v1/mcp-servers` | [`examples/`](examples/) |
| Grant MCP tool access | `POST /api/v1/mcp-servers/{name}/grants` | [`examples/mcp-tool-grant-*.json`](examples/) |
| Write audit event | `POST /audit_log/` | OpenAPI |
| Kill switch | `POST /agent_set_status/` | [`examples/agent-kill-switch-disable.json`](examples/) |

## Runnable tutorial

Copy-paste scripts + local gateway simulator: [kimss-python-quickstart](https://github.com/kimss-ai/kimss-python-quickstart).

## Related

- https://kimss.ai/docs/route_traffic
- [docs/anthropic-onboarding.md](docs/anthropic-onboarding.md)
- [docs/decision-maker-brief.md](docs/decision-maker-brief.md) ג€” buyer / security overview (not required for wiring)
- [kimss-python-sdk](https://github.com/kimss-ai/kimss-python-sdk) ג€” optional `pip install kimss`
- [kimss.ai/trust](https://kimss.ai/trust)
