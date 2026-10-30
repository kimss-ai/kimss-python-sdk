# KIMSS GATEWAY AGENT INSTRUCTIONS

Dual-listener Secure AI Gateway. Never “zero-trust”.

**Prerequisites (Kimss app) — gated order:**

1. Provider Vault (`https://kimss.ai/app/vault`) — store the provider key; never paste it in chat.
2. Gateway API key (`https://kimss.ai/app/keys`) — set `KIMSS_API_KEY`; never paste the full key in chat.
3. Wire native SDK base URL + `X-Kimss-Agent-Id`; one live 200.
4. Confirm the agent on `https://kimss.ai/app/agents` (Production+: may be quarantined until an admin enables).
5. Enforce: CI lint against direct provider base URLs; hand admin the provider-lock / egress checklist (`/docs/enforcement`).

There is **no sanctioned client fallback** to the provider when the gateway is down.

1. Keep the developer's native `openai` or `anthropic` SDK.
2. OpenAI → `base_url=https://api.kimss.ai/v1`. Anthropic → `base_url=https://api.kimss.ai`.
3. Always inject `X-Kimss-Agent-Id` / `X-Kimss-Agent-Name`.
4. Never use `KimssClient` for chat/completions/messages.
5. Kill switch: `agent_disabled`. Unvaulted model on paid: `shadow_agent_blocked`. Keys: `kimss_...`.

See [AI_INTEGRATION.md](../AI_INTEGRATION.md).
