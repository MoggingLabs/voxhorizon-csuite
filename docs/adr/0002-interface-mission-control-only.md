# ADR 0002: Mission Control is the only interface

- Status: Accepted
- Date: 2026-05-23

## Context

Early designs assumed Telegram (and possibly Slack) as agent channels. The owner
wants a single pane of glass and no chat-app sprawl.

## Decision

The only interface is Mission Control, an Agents module on the Data Brain Next.js
app plus a dispatcher. No Telegram, no Slack, no Discord. Agent channel configs
are empty.

## Consequences

Agents become passive (no listening gateway); they are driven by the dispatcher.
This removes per-agent bot tokens and simplifies the surface, and it pairs with
the fault-isolation and dispatch decisions (ADR 0004, 0005). It also means there
is no out-of-band way to reach an agent; Mission Control must stay available.
