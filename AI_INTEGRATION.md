# AI Integration — pointer (not the contract)

**Canonical public A2A contract.** Fetch this URL when onboarding a customer app. Do not treat this file as the spec, and do not clone the control-plane repo into the customer app.

```text
https://raw.githubusercontent.com/kimss-ai/kimss-control-plane/main/AI_INTEGRATION.md
```

Hub: [kimss-ai/kimss-control-plane](https://github.com/kimss-ai/kimss-control-plane)

## Before repo changes

1. Provider Vault (`/app/vault`) — each model is a `custom:<model_id>` alias.
2. Gateway API key (`/app/keys`) — a `kimss_...` workspace key, not the provider key.

## What a coding agent should do

- Existing OpenAI or Anthropic app: keep that client. Set the Kimss base URL, the Gateway key, the vaulted model alias, and `X-Kimss-Agent-Id`.
- No LLM client yet: `pip install kimss-forge` and `gateway="kimss"`. Repo: https://github.com/kimss-ai/kimss-forge
- Do **not** `pip install kimss` or add Maven `com.kimss:kimss-java` to route chat. Those control-plane clients are deprecated for new onboarding.
- HTTP **451**, or a tool result `policy_violation` / `authority_boundary`, means Guardrails fired after the route worked. Do not change `base_url`. Follow the Guardrails section in the canonical file and https://kimss.ai/docs/trust_safety
