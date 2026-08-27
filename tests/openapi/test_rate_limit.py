from __future__ import annotations

from pathlib import Path

from gerpgo_sdk.common.rate_limit import PersistentRateLimiter


def test_rate_limiter_waits_across_instances(tmp_path: Path) -> None:
    now = [100.0]
    sleeps: list[float] = []

    def clock() -> float:
        return now[0]

    def sleep(seconds: float) -> None:
        sleeps.append(seconds)
        now[0] += seconds

    first = PersistentRateLimiter(tmp_path, clock=clock, sleeper=sleep)
    first.wait("product-performance", 60.0)
    now[0] += 10.0
    second = PersistentRateLimiter(tmp_path, clock=clock, sleeper=sleep)
    second.wait("product-performance", 60.0)

    assert sleeps == [50.0]
