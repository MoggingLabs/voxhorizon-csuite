# ADR 0001: Runtime is Hermes, not OpenClaw

- Status: Accepted
- Date: 2026-05-23

## Context

The License-and-Scale agent templates assume an OpenClaw runtime, which is not in
production use here. Production runs Hermes (`ghcr.io/hostinger/hvps-hermes-agent`)
and the team knows it. Standing up OpenClaw would be a net-new, unproven runtime.

## Decision

Run the C-Suite agents on Hermes, as our own containers from the public Hermes
image, isolated from production. Port each agent persona into a Hermes `SOUL.md`.

## Consequences

We reuse a proven runtime, multi-channel support, native delegation, and the
production deploy patterns. The L-S Mission Control (OpenClaw-specific) is dropped
in favor of a Hermes-oriented Mission Control. Agent personas are authored as
Hermes SOUL files rather than OpenClaw profiles.
