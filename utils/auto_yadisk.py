from __future__ import annotations

import logging
import os
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

from config.settings import CONFIG
from utils.backup import backup_sqlite_db
from utils.user_prefs import load_prefs, get_current_db_path


logger = logging.getLogger(__name__)


def _seconds_until(dt: datetime) -> float:
    now = datetime.now()
    return max(0.0, (dt - now).total_seconds())


def _next_trigger_time(hours: list[int]) -> datetime:
    now = datetime.now()
    today_hours = sorted(hours)
    for h in today_hours:
        candidate = now.replace(hour=h, minute=0, second=0, microsecond=0)
        if candidate > now:
            return candidate
    # next day first hour
    first = today_hours[0]
    next_day = (now + timedelta(days=1)).replace(
        hour=first, minute=0, second=0, microsecond=0
    )
    return next_day


def _upload_job() -> None:
    try:
        prefs = load_prefs()
        remote_dir = (
            prefs.yandex_remote_dir
            or CONFIG.yandex_default_remote_dir
            or "/SdelkaBackups"
        ).strip()
        token = (
            os.environ.get("YADISK_OAUTH_TOKEN")
            or prefs.yandex_oauth_token
            or CONFIG.yandex_default_oauth_token
            or ""
        ).strip()
        if not token:
            logger.warning(
                "Auto Yadisk: пропуск — токен не задан ни в настройках, ни в CONFIG"
            )
            return
        src_db = Path(get_current_db_path())
        backup_path = backup_sqlite_db(src_db)
        if not backup_path:
            logger.error(
                "Auto Yadisk: не удалось создать локальный бэкап — выгрузка пропущена"
            )
            return
        from utils.yadisk import YaDiskClient, YaDiskConfig

        client = YaDiskClient(YaDiskConfig(oauth_token=token, remote_dir=remote_dir))
        remote_path = client.rotate_and_upload(
            Path(backup_path),
            canonical_name="sdelka_base.db",
            backup_prefix="backup_base_sdelka_",
            max_keep=20,
        )
        logger.info("Auto Yadisk: выгрузка завершена: %s", remote_path)
    except Exception as exc:
        logger.exception("Auto Yadisk: ошибка выгрузки: %s", exc)


def _scheduler_loop(hours: list[int]) -> None:
    # Simple loop: sleep until next trigger, run once, repeat
    while True:
        try:
            target = _next_trigger_time(hours)
            secs = _seconds_until(target)
            # Sleep in one chunk; OS sleep is efficient and nearly zero CPU
            time.sleep(secs)
            _upload_job()
        except Exception as exc:
            logger.exception("Auto Yadisk: ошибка в цикле планировщика: %s", exc)
            # небольшая пауза, чтобы избежать tight loop при постоянных исключениях
            time.sleep(5)


def start_yadisk_upload_scheduler() -> None:
    """Start background daemon scheduler for timed Yandex uploads.

    Triggers at 08:00, 10:00, 12:00, 14:00, 16:00, 18:00 local time.
    """
    hours = [8, 10, 12, 14, 16, 18]
    th = threading.Thread(
        target=_scheduler_loop, args=(hours,), daemon=True, name="YadiskScheduler"
    )
    th.start()
    logger.info("Auto Yadisk: планировщик запущен на часы %s", hours)
