from scripts.p08_lab_protocol import redis_ping_invocation


def test_redis_probe_never_places_the_secret_in_argv() -> None:
    secret = "CANARY_P08_REDIS_ARGV"
    environment, argv = redis_ping_invocation(secret)
    assert environment == {"REDISCLI_AUTH": secret}
    assert argv == ["redis-cli", "ping"]
    assert all(secret not in item for item in argv)
