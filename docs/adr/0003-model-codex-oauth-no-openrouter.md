# ADR 0003: Model is OpenAI via the Codex OAuth subscription, no OpenRouter

- Status: Accepted
- Date: 2026-05-23

## Context

The production operator config carries `base_url: https://openrouter.ai/api/v1`,
which raised the question of whether OpenAI is reached through OpenRouter. Live
inspection of the operator showed `auth.json` `active_provider=openai-codex` as
the only provider and no OpenRouter or OpenAI key in the environment. The owner
wants the subscription used directly, never OpenRouter.

## Decision

Agents use `provider: openai-codex` with model `gpt-5.5`, authenticated by a
ChatGPT/Codex OAuth `auth.json`. All OpenRouter references are scrubbed: no
`base_url: openrouter`, no `openrouter:` block, no OpenRouter key, no
`OPENAI_API_KEY`.

## Consequences

Flat subscription cost rather than metered API, no third party in the data path.
The `auth.json` is a credential file handled like a secret. A test
(`sec_grep_no_openrouter`, `sec_no_api_key_env`, `sec_active_provider_codex`)
enforces the scrub. Subscription rate limits apply across all agents.
