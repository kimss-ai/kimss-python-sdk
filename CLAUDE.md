# Kimss Python SDK — Claude Code

Read [AI_INTEGRATION.md](AI_INTEGRATION.md) (canonical public: [kimss-control-plane](https://raw.githubusercontent.com/kimss-ai/kimss-control-plane/main/AI_INTEGRATION.md)).

Dual-listener: OpenAI `/v1/chat/completions` and Anthropic `/v1/messages`. Keep the native SDK already in the repo. Never use `KimssClient` or `pip install kimss` for new gateway onboarding. A new Python agent is `pip install kimss-forge` with `gateway="kimss"`. Always send `X-Kimss-Agent-Id`. HTTP 451 and tool `policy_violation` / `authority_boundary` are Guardrails, not a bad base URL.
