from __future__ import annotations


def redis_ping_invocation(secret: str) -> tuple[dict[str, str], list[str]]:
    """Return the lab Redis probe without placing its secret in argv."""
    return {"REDISCLI_AUTH": secret}, ["redis-cli", "ping"]
