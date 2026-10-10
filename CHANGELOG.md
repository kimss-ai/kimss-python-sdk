# Changelog

All notable changes to the **kimss** PyPI package are documented here. The canonical source for this file in development is the monorepo path `kimss_sdk/CHANGELOG.md`.

## [2.2.0] — 2026-10-10

### Added

- **`KimssProxy`** (`kimss.proxy`): Invisible Proxy helper that auto-mints `X-Kimss-Run-Id` / lineage for OpenAI and Anthropic SDKs (`proxy.openai()`, `proxy.anthropic()`, or `proxy.chat_completions()`). Use `proxy.delegate(agent_id=...)` for the child hop. Example: [examples/00c_proxy_auto_lineage.py](examples/00c_proxy_auto_lineage.py).
- **`RunContext`** helpers on `kimss.run_context` / package exports for declared multi-agent runs without Kimss Forge.

## [2.1.1] — 2026-08-21

### Added

- Dual-listener inbound guide: official Anthropic SDK at `base_url=https://api.kimss.ai` → `POST /v1/messages`, with `X-Kimss-Agent-Id` ([AI_INTEGRATION.md](AI_INTEGRATION.md), [GETTING_STARTED.md](GETTING_STARTED.md), [examples/00b_anthropic_proxy.py](examples/00b_anthropic_proxy.py)).

### Fixed

- Docs no longer say the Anthropic SDK is not an inbound drop-in. Azure official clients remain vault-only backends.

## [2.1.0] — 2026-08-21

### Deprecated

- **Inference wrappers:** `KimssClient.chat`, `Agent.query` / `Agent.run`, `agents.run`, `models.create`, `images.generate`, and MCP tools `kimss_chat` / `kimss_run_agent` / `kimss_complete` emit `DeprecationWarning`. Prefer the official OpenAI SDK with `base_url=https://api.kimss.ai/v1` and `X-Kimss-Agent-Id` headers ([AI_INTEGRATION.md](AI_INTEGRATION.md)).

### Changed

- Package repositioned as a **control-plane / DevOps** client (`agents.register`, `usage.report`). Docs and A2A files lead with the gateway proxy pattern.

## [2.0.2] — 2026-08-16

### Changed

- Docs and MCP server description no longer mention hosted vector stores. File upload is ephemeral (single-turn attachments). Hosted RAG routes return HTTP 410.

## [2.0.1] — 2026-07-24

### Fixed

- **`client.models.create`:** accept optional ``prompt=`` as an alias for a single user message. Call sites that mirrored ``agents.run(..., prompt=...)`` no longer raise ``TypeError: unexpected keyword argument 'prompt'``.

## [2.0.0] — 2026-06-03

### Breaking

- **Python parameters:** `thread_id` was renamed to **`conversation_id`** everywhere in the public SDK (`KimssClient.chat`, `Agent.query`, `client.agents.run`, and MCP tool arguments `kimss_chat` / `kimss_run_agent`). Integrators must rename keyword arguments; positional usage of the second message argument is unchanged for `agents.run(assistant_id, message, ...)`.
- **Semantics:** Kimss agent execution is backed by **Azure AI Foundry 2.x** — **conversations** and the **Responses** API replace classic **threads / runs** shapes. The HTTP JSON field on the wire remains **`thread_id`** (historical name) for the Foundry conversation id; the SDK maps **`conversation_id`** → `thread_id` in request bodies.
- **`AgentRunResult`:** Prefer **`.conversation_id`** for the id returned in `res` (still often keyed as `thread_id` in JSON until a future API revision). Typed access clarifies that this is a **conversation** id, not a legacy Assistants “thread” object.

### Non-breaking

- **Wire format:** No change required to Kimss REST bodies if you call the API directly — `thread_id` in JSON is still the field name for continuing a conversation.

## [1.1.0] and earlier

See [GitHub releases](https://github.com/kimss-ai/kimss-python-sdk/releases) for older package history on the public mirror.
