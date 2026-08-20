import time
from collections.abc import Callable
from typing import TypeVar

import httpx

T = TypeVar("T")

NETWORK_ERRORS: tuple[type[BaseException], ...] = (
    httpx.RemoteProtocolError,
    httpx.ConnectError,
    httpx.ReadError,
)

MAX_ATTEMPTS = 3
RETRY_WAIT_SEC = 0.2

_httpx_retry_installed = False


def call_with_retry(func: Callable[[], T]) -> T:
    """Idle 切断など一過性の通信エラーを最大2回リトライする。"""
    last_error: BaseException | None = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return func()
        except NETWORK_ERRORS as exc:
            last_error = exc
            print(
                f"[supabase retry {attempt}/{MAX_ATTEMPTS}] "
                f"{type(exc).__name__}: {exc}"
            )
            if attempt == MAX_ATTEMPTS:
                break
            time.sleep(RETRY_WAIT_SEC)

    assert last_error is not None
    raise last_error


def install_httpx_retry() -> None:
    """
    supabase-py が使う httpx.Client.send をラップし、
    Auth / PostgREST 双方の idle 切断を共通リトライする。
    """
    global _httpx_retry_installed
    if _httpx_retry_installed:
        return

    original_send = httpx.Client.send

    def send(self, request: httpx.Request, *args, **kwargs):  # type: ignore[no-untyped-def]
        return call_with_retry(lambda: original_send(self, request, *args, **kwargs))

    httpx.Client.send = send  # type: ignore[method-assign]
    _httpx_retry_installed = True
