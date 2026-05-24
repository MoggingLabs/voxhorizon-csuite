"""Single-operator auth gate (fail-closed).

A login checks MC_AUTH_PASS and sets an HMAC-signed session cookie keyed on
MC_AUTH_SECRET. If either secret is unset, the gate denies everything.
"""

from __future__ import annotations

import hmac
from hashlib import sha256

COOKIE = "mc_session"
_VALUE = "ok"


def _sign(value: str, secret: str) -> str:
    return hmac.new(secret.encode(), value.encode(), sha256).hexdigest()


def make_session(secret: str) -> str:
    return f"{_VALUE}.{_sign(_VALUE, secret)}"


def valid_session(cookie: str | None, secret: str) -> bool:
    if not secret or not cookie or "." not in cookie:
        return False
    value, _, sig = cookie.partition(".")
    return value == _VALUE and hmac.compare_digest(sig, _sign(_VALUE, secret))


def password_ok(supplied: str, auth_pass: str) -> bool:
    if not auth_pass:
        return False
    return hmac.compare_digest(supplied or "", auth_pass)
