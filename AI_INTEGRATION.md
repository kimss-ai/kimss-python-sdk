# AI Integration — Kimss Control Plane (Agent-to-Agent)

**Canonical public A2A contract** for Cursor, Cascade, Claude Code, Windsurf, Devin, and other coding assistants.

If the user gave you **only this repo link** (or said “onboard Kimss” without a Gateway key / vaulted model), run the guided workflow in **[ONBOARDING.md](https://raw.githubusercontent.com/kimss-ai/kimss-control-plane/main/ONBOARDING.md)** first — welcome, collect key and model, then return here to wire.

**Fetch URL (always prefer this over cloning):**

```text
https://raw.githubusercontent.com/kimss-ai/kimss-control-plane/main/AI_INTEGRATION.md
```

Kimss is a **Model-Agnostic Enterprise AI Gateway and Governance Control Plane** with a **dual-listener** inbound proxy:

| Listener | Method | URL |
|----------|--------|-----|
| OpenAI syntax | `POST` | `https://api.kimss.ai/v1/chat/completions` |
| Anthropic syntax | `POST` | `https://api.kimss.ai/v1/messages` |

Runtime SSOT remains `kimssApi`. This repo is the **public contract hub** — **do not clone** control-plane source into the customer app. Rewire the **customer** codebase only.

Product companion: https://kimss.ai/docs/route_traffic

---

## What to install

| Situation | Do this |
|-----------|---------|
| App already uses OpenAI, Anthropic, LangChain, or another OpenAI-compatible client | Keep that client. Change base URL, Gateway key, vaulted model alias, and `X-Kimss-Agent-Id`. |
| No LLM client yet, and the user wants a new Python agent | `pip install kimss-forge`, then `gateway="kimss"` with `agent_id` and `workspace_key`. Repo: https://github.com/kimss-ai/kimss-forge |
| Java, Node, or any other language (Path A chat) | Vendor SDK or plain HTTP. JDK `HttpClient` sample: https://kimss.ai/docs/route_traffic |
| **Optional — swarm / multi-agent trees** (Observe/Enforce) | Lineage client: Forge `delegate`, Python `pip install "kimss>=2.2.0"` + `KimssProxy`, or Java `ai.kimss:kimss-java` ≥0.3.0 + `KimssProxy`. See [Swarm lineage](#swarm-lineage-optional). |
| Do **not** do this for Path A chat | `KimssClient` / `AgentsApi.run` (or legacy chat helpers) for inference. Those are **deprecated** for gateway onboarding. |

Optional IDE MCP (`kimss-mcp-server`) is a separate extra. It is not required to route an application.

---

## Cascade / coding-agent procedure (follow in order)

When the user asks you to onboard a repo to Kimss (or “route traffic through the Kimss gateway”):

1. **Confirm prerequisites** (user should already have done these in the Kimss UI). If not, stop and tell them to complete:
   - Provider Vault (`/app/vault`) — each model they call must exist as `custom:<model_id>`
   - Gateway API key (`/app/keys`) — a `kimss_...` workspace key (not the provider key)
2. **Detect** whether the codebase uses OpenAI-compatible clients, Anthropic clients, or both (SDK imports, `OPENAI_*` / `ANTHROPIC_*` env, LangChain/Vercel AI `baseURL`, raw `fetch` to `api.openai.com` / `api.anthropic.com`).
3. **Choose the client** using [What to install](#what-to-install). If an OpenAI or Anthropic client already exists, keep it for Path A. Never add `KimssClient` / `AgentsApi.run` for chat. If there is no LLM client and the user wants a new Python agent, add Kimss Forge (`pip install kimss-forge`, `gateway="kimss"`). Add `KimssProxy` (Python or Java) **only** when the user wants swarm lineage ([Swarm lineage](#swarm-lineage-optional)).
4. **Point the client at Kimss** (skip when using Kimss Forge — `gateway="kimss"` sets the listener):
   - OpenAI-compatible → `base_url` / `baseURL` = `https://api.kimss.ai/v1`
   - Anthropic → `base_url` / `baseURL` = `https://api.kimss.ai` (**no** `/v1/messages` suffix — the SDK appends it)
5. **Swap the API key** to the Gateway `kimss_...` key via env (`OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `KIMSS_API_KEY`). For Kimss Forge pass `workspace_key="kimss_..."` (do not put the provider key there). Never commit provider keys.
6. **Map models** to the exact vaulted alias the user names (`custom:your-model-id` as saved in Provider Vault). Do not invent an id by prefixing `custom:` onto a model name already in the repo. A **400** that says the model is not registered means that id is not in Vault — stop and use the id shown on `/app/vault`. Do not change `base_url` to clear it.
7. **Always send** `X-Kimss-Agent-Id` (and preferably `X-Kimss-Agent-Name`) on inference. Pick a stable slug per service (e.g. `billing-bot`). On Python, put that dict in the client constructor as `default_headers`, or pass `extra_headers` to `.create()`. **Never** pass a parameter named `headers` to `chat.completions.create()` or `messages.create()` — the SDK raises `TypeError: unexpected keyword argument 'headers'` and the request never leaves the process. Node uses `defaultHeaders` on the client. Raw HTTP uses the header itself.
8. **Forward headers** through any HTTP interceptor / proxy / Hermis-style middleware — never strip Kimss agent headers.
9. **If the user also needs internal MCP** (their HTTPS MCP servers behind Kimss): follow [Internal MCP routing](#internal-mcp-routing) and [docs/mcp-routing.md](docs/mcp-routing.md). Do **not** confuse this with optional `kimss-mcp-server` (IDE → Kimss API).
10. **Verify** (see [Verification](#verification-after-wiring) below). Do not claim success until a live call works or the user confirms Vault + key + model alias.
11. **If the call is blocked by policy**, follow [Guardrails](#guardrails-do-not-fix-these-by-changing-the-client). Do not change `base_url` or install a Kimss SDK to clear HTTP 451 or a tool-argument error.

---

## Prerequisites (Kimss app — before repo changes)

1. **Provider Vault** (`/app/vault`): register each `custom:<model_id>` you will call. One vault row per model alias; you may reuse the same provider API key across models.
2. **Gateway API key** (`/app/keys`): mint a `kimss_...` workspace key.
3. **Route traffic** in the app: base URL + Gateway key + agent headers (this file).

If a model is not vaulted, Kimss returns an error pointing to Provider Vault. **Agents** (`/app/agents`) populate automatically after the first governed request that includes `X-Kimss-Agent-Id` — you do **not** need to create agents in the UI first.

---

## Rules (do not violate)

1. **Never** use a custom `KimssClient` for chat/completions/messages or any LLM inference.
2. **Keep** the codebase’s native OpenAI or Anthropic SDK (or OpenAI-compatible HTTP client) — zero data-plane refactoring.
3. **OpenAI:** `base_url` = `https://api.kimss.ai/v1`.
4. **Anthropic:** `base_url` = `https://api.kimss.ai` only.
5. **Always** inject `X-Kimss-Agent-Id` (preferably also `X-Kimss-Agent-Name`) for JIT inventory, audit, spend attribution, and kill-switch. Omitting it may still proxy, but agents appear as unattributed / model-labelled shadow rows and kill-switch by name is weaker.
6. **Call-site visibility:** pass a plain dict with `X-Kimss-Agent-Id` (and `X-Kimss-Agent-Name`) as `default_headers` on the client, or as `extra_headers` on `.create()`. The argument name is not `headers`. Do not install a Kimss package just to build that dict (Path A).
7. **Streaming** works the same (`stream=True` / `stream: true`) — keep Kimss base URL and headers.
8. **Control-plane API** (registry, MCP RBAC, audit, metering, kill switch): use [`openapi/control-plane.yaml`](openapi/control-plane.yaml) — not chat endpoints. OpenAPI does **not** duplicate inference paths; this file is the inference contract. MCP register/grant shapes are in that spec; step-by-step MCP: [docs/mcp-routing.md](docs/mcp-routing.md).
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

You still must attach `X-Kimss-Agent-Id` in code or middleware — env alone does not add headers for most SDKs.

## SDK keyword names

The OpenAI and Anthropic Python SDKs do not accept `headers=` on `.create()`. That fails in the customer process, before any request reaches Kimss:

```text
TypeError: Completions.create() got an unexpected keyword argument 'headers'
```

| SDK | Client constructor | Per-call `.create()` |
|-----|--------------------|----------------------|
| OpenAI Python | `default_headers={...}` | `extra_headers={...}` |
| Anthropic Python | `default_headers={...}` | `extra_headers={...}` |
| OpenAI Node | `defaultHeaders: {...}` | do not pass `headers` |
| cURL / raw HTTP | `X-Kimss-Agent-Id` request header | — |

Prefer `default_headers` / `defaultHeaders` on the client so tool loops keep the same agent id. If the client is already constructed, add `extra_headers=` on the existing `.create()` call. Do not rename that argument to `headers`.

---

## OpenAI (Python)

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://api.kimss.ai/v1",  # required
    api_key="kimss_workspace_key",  # Gateway key — not the provider key
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

If the `OpenAI(...)` client already exists and you are only editing the call, the per-call keyword is `extra_headers` (not `headers`):

```python
response = client.chat.completions.create(
    model="custom:your-model-id",
    messages=[{"role": "user", "content": "Execute audit."}],
    extra_headers={"X-Kimss-Agent-Id": "my-service"},
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

1. Make one non-stream chat/completions or messages call with the vaulted `custom:…` model.
2. Expect **200** and a normal assistant payload (not HTML login pages).
3. In Kimss UI: **Agents** (`/app/agents`) shows the `X-Kimss-Agent-Id` after the first call.
4. Optional meter check:

```bash
curl -s -H "Authorization: Bearer kimss_..." \
  https://api.kimss.ai/api/v1/governed-requests/meter
```

Shape: [`examples/governed-requests-meter-response.json`](examples/governed-requests-meter-response.json).

A policy denial (below) still counts as “the route works.” Report the policy to the user. Do not rewrite the client.

---

## Guardrails (do not fix these by changing the client)

Workspace policies at `/app/guardrails` run **after** the gateway accepts the call. Customer doc: https://kimss.ai/docs/trust_safety

Web Search and Internal MCP start **off**. A hello-world chat completion does not need either. Do not enable them unless the user asked.

| Result | Meaning | What you should do |
|--------|---------|--------------------|
| HTTP **451** `content_safety` or `prompt_injection` | Content safety or Prompt Shields | Leave the client. The admin adjusts Guardrails or the prompt. |
| HTTP **451** `pii_scrub` | PII block (Production+). Alert mode returns **200** and still logs an intercept. | Same. Do not strip the Gateway key out of the request to “avoid PII.” |
| HTTP **451** `safety_check_failed` | Safety backend failed closed | Not a bad API key. Do not retry in a loop. |
| HTTP **403** `web_search_disabled` | Web Search is off | Chat without that tool. Do not flip the workspace opt-in unless asked. |
| HTTP **403** `mcp_disabled` | Internal MCP is off | Only continue to [Internal MCP routing](#internal-mcp-routing) if the user asked to call their MCP servers. |
| HTTP **403** `agent_disabled` | Kill switch | Re-enable under **Agents**, or send a different `X-Kimss-Agent-Id`. |
| HTTP **200** tool JSON `error: policy_violation` | Argument shape rule (allowlist, regex, exact, max length, deny pattern) | The chat call succeeded. Change the tool arguments or the rule. Do not rewrite the HTTP client. |
| HTTP **200** tool JSON `error: authority_boundary` | Trusted source: a model- or tool-supplied value was blocked | The human must name the value this turn. Not a wiring bug. |
| HTTP **200** `hitl_pending` (or **409** with `X-Kimss-Hitl-Protocol: interrupt`) on `POST /v1/agents/run` | Approvals for an irreversible tool (Scale+) | Resume the same thread after approve. Invisible Proxy `POST /v1/chat/completions` does not run this pause. |

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `TypeError` … `unexpected keyword argument 'headers'` | Passed `headers=` to `.create()` | Use `default_headers` on the client, or `extra_headers` on `.create()`. See [SDK keyword names](#sdk-keyword-names). |
| `401` / invalid API key | Wrong or missing `kimss_...` key | Mint under **Gateway → Keys** (`/app/keys`) |
| `400` / missing agent / attribution errors | Header stripped or empty where required by a path | Set `X-Kimss-Agent-Id` on every inference call |
| `403` / `agent_disabled` | Kill switch | Re-enable under **Governance → Agents** |
| `429` / `governed_requests_exhausted` | Monthly allowance | Check meter or [pricing](https://kimss.ai/pricing) |
| `429` / `custom_endpoint_cap_exceeded` | Vault token cap | Raise/disable cap on the vaulted endpoint |
| Model not found / vault error | Model not registered as `custom:…` | Vault under `/app/vault`; match the exact model string |
| Anthropic path errors | `base_url` includes `/v1/messages` | Use `https://api.kimss.ai` only |
| OpenAI 404 on `/chat/completions` | Used Anthropic base without `/v1` | OpenAI must use `https://api.kimss.ai/v1` |
| HTTP **451** | Guardrails (content safety, prompt attack, PII, safety backend) | Wiring succeeded. See [Guardrails](#guardrails-do-not-fix-these-by-changing-the-client). Do not change `base_url`. |
| HTTP **200** with tool `policy_violation` or `authority_boundary` | Argument rule or Authority Boundary | Wiring succeeded. Fix the tool value or the rule under `/app/guardrails`. |
| MCP register/call blocked | Guardrails Internal MCP off | Enable under `/app/guardrails` only if the user asked; see [docs/mcp-routing.md](docs/mcp-routing.md) |

---

## Internal MCP routing

**Path A — your MCP servers behind Kimss (governed):** register HTTPS MCP under `/api/v1/mcp-servers`, enable Guardrails **Internal MCP**, attach tools on the agent, optional grants/argument policies. Hermis calls `mcp__{server}__{tool}`. Full procedure: **[docs/mcp-routing.md](docs/mcp-routing.md)**.

**Path B — IDE talks to Kimss as MCP tools (optional):** `pip install 'kimss[mcp]'` / `kimss-mcp-server` — see https://kimss.ai/docs/python_sdk_mcp. That does **not** replace Path A and is **not** required for gateway chat.

Minimal Path A register:

```bash
curl -sS -X POST "https://api.kimss.ai/api/v1/mcp-servers" \
  -H "Authorization: Bearer kimss_..." \
  -H "Content-Type: application/json" \
  -d @examples/mcp-server-register.json
```

Then discover, attach tools in the Agents UI, and optionally upsert grants (`examples/mcp-tool-grant-*.json`).

---

## Swarm lineage (optional)

Path A (native OpenAI/Anthropic) does **not** send declared-run headers. Without them, Guardrails swarm mode should stay **Off** — metering, kill switch, and content Guardrails still apply.

When the user wants **Observe** or **Enforce** trees on [Swarm Runs](https://kimss.ai/app/runs), wire **one** lineage path (setup-once; toggle mode later without redeploy):

### Python — Kimss Forge

```python
# pip install kimss-forge
from kimss_forge import Agent
agent = Agent(gateway="kimss", agent_id="orchestrator", workspace_key="kimss_...")
child = agent.delegate(agent_id="researcher", model="custom:your-model")
```

### Python — Invisible Proxy (`KimssProxy`)

```python
# pip install "kimss>=2.2.0" openai
from kimss.proxy import KimssProxy
proxy = KimssProxy(api_key="kimss_...", agent_id="orchestrator")
client = proxy.openai()
client.chat.completions.create(model="custom:your-model", messages=[...])
proxy.delegate(agent_id="researcher")
client.chat.completions.create(...)
```

### Java — Invisible Proxy (`KimssProxy`)

```java
// Maven: ai.kimss:kimss-java >= 0.3.0
KimssProxy proxy = KimssProxy.builder()
    .apiKey(System.getenv("KIMSS_API_KEY"))
    .agentId("orchestrator")
    .build();
proxy.chatCompletions("custom:your-model", List.of(Map.of("role", "user", "content", "...")));
proxy.delegate("researcher");
```

Or keep OpenAI OkHttp and pass `proxy.requestHeaders()` / `absorbResponseHeaders(...)` on each call.

### Advanced — BYO orchestrator

Forward `X-Kimss-Run-Id`, `X-Kimss-Depth`, `X-Kimss-Parent-Span`, `X-Kimss-Span-Id`, `X-Kimss-Lineage` from each response onto the next hop. Product doc: https://kimss.ai/docs/delegation_governance

**Demo without customer code:** `/app/runs` → **Run a demo swarm**.

---

## Deprecated control-plane chat clients

`KimssClient` chat/run and `AgentsApi.run` are **deprecated for Path A inference**. Do not use them while wiring chat.

The same packages still provide **optional** swarm helpers: Python `KimssProxy` ([kimss-python-sdk](https://github.com/kimss-ai/kimss-python-sdk), PyPI `kimss>=2.2.0`) and Java `KimssProxy` ([kimss-java-sdk](https://github.com/kimss-ai/kimss-java-sdk), `ai.kimss:kimss-java` ≥0.3.0). Registry helpers (`agents.register`, `usage.report`) remain for existing callers. New Python agent loops: [Kimss Forge](https://github.com/kimss-ai/kimss-forge).

## Kill switch

HTTP **403** with `agent_disabled` (OpenAI `error.code` or Anthropic error body). Applies to MCP tool hops in Hermis as well.

## Control-plane quick path

| Task | Endpoint | Doc |
|------|----------|-----|
| Check monthly cap | `GET /api/v1/governed-requests/meter` | OpenAPI |
| Register MCP server | `POST /api/v1/mcp-servers` | [docs/mcp-routing.md](docs/mcp-routing.md), [`examples/mcp-server-register.json`](examples/mcp-server-register.json) |
| Discover MCP tools | `POST /api/v1/mcp-servers/{name}/discover` | [docs/mcp-routing.md](docs/mcp-routing.md) |
| Grant MCP tool access | `PUT /api/v1/mcp-servers/{name}/grants` | [`examples/mcp-tool-grant-*.json`](examples/) |
| Write audit event | `POST /audit_log/` | OpenAPI |
| Kill switch | `POST /agent_set_status/` | [`examples/agent-kill-switch-disable.json`](examples/) |

## Runnable tutorial

Copy-paste gateway scripts (native clients, not the deprecated control-plane SDKs): [kimss-python-quickstart](https://github.com/kimss-ai/kimss-python-quickstart).

New Python agent loop: [kimss-forge](https://github.com/kimss-ai/kimss-forge) (`pip install kimss-forge`).

## Related

- https://kimss.ai/docs/route_traffic
- https://kimss.ai/docs/trust_safety
- https://kimss.ai/docs/agent_harness
- https://kimss.ai/open-source
- https://kimss.ai/docs/routing_internal_mcp_servers
- [docs/mcp-routing.md](docs/mcp-routing.md)
- [docs/anthropic-onboarding.md](docs/anthropic-onboarding.md)
- [docs/decision-maker-brief.md](docs/decision-maker-brief.md) — buyer / security overview (not required for wiring)
- [kimss.ai/trust](https://kimss.ai/trust)
