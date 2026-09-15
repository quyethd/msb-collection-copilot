"""Entrypoint for the Zalo Bot Platform polling worker service.

Single-poller guard: an exclusive lock ensures only one polling worker runs
for the shared bot token. The token is read from a root-readable file and is
never present in process arguments or logs.
"""
from __future__ import annotations

import fcntl
import logging
import os
import signal
import time
from pathlib import Path

from msb_zalo.client import ZaloBotClient
from msb_zalo.worker import ZaloPollingWorker, preflight

_PROJECT_ROOT = Path(__file__).resolve().parent
LOCK_FILE = str(_PROJECT_ROOT / ".zalo-worker.lock")


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def _acquire_lock():
    handle = open(LOCK_FILE, "a+")
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        handle.close()
        raise RuntimeError("Another Zalo polling worker is already running")
    return handle


def main() -> None:
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"), format="%(levelname)s %(name)s %(message)s")
    logger = logging.getLogger("msb.zalo_worker")
    lock = _acquire_lock()
    try:
        token_file = os.environ.get("ZALO_BOT_TOKEN_FILE", "/root/.config/msb-collection/zalo-bot-token")
        secret_file = os.environ.get("ZALO_INBOUND_SHARED_SECRET_FILE", "/root/.config/msb-collection/zalo-inbound-shared-secret")
        inbound_url = os.environ.get("MSB_ZALO_INBOUND_URL", "http://127.0.0.1:18080/demo/zalo/inbound")
        poll_timeout = _int_env("MSB_ZALO_POLL_TIMEOUT", 30)
        heartbeat_file = os.environ.get("MSB_ZALO_HEARTBEAT_FILE", "") or None
        watermark_file = os.environ.get("MSB_ZALO_WATERMARK_FILE", str(_PROJECT_ROOT / "build" / "zalo-update-watermark.json"))
        client = ZaloBotClient(token_file=token_file, timeout=float(poll_timeout) + 20.0)
        gate = preflight(client)
        logger.info("zalo preflight ok (bot=%s webhook_configured=%s)", gate["bot_id"], gate["webhook_configured"])
        worker = ZaloPollingWorker(
            client,
            inbound_url=inbound_url,
            secret_file=secret_file,
            poll_timeout=poll_timeout,
            heartbeat_file=heartbeat_file,
            watermark_file=watermark_file,
        )
        worker.validate()
        logger.info("zalo worker starting (poll_mode=direct)")
        worker.start()

        def _request_stop(signum: int, _frame) -> None:
            logger.info("zalo worker stopping (poll_mode=direct, signal=%s)", signum)
            worker.stop(timeout=10.0)

        signal.signal(signal.SIGTERM, _request_stop)
        signal.signal(signal.SIGINT, _request_stop)
        while worker.is_alive():
            time.sleep(0.5)
        logger.info("zalo worker stopped")
    finally:
        lock.close()


if __name__ == "__main__":
    main()
