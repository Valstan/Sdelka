from __future__ import annotations

import json
import time
from typing import Dict, List

from config.settings import CONFIG
from utils.text import normalize_for_search

import logging

_HISTORY_PATH = CONFIG.logs_dir / "usage_history.json"
_MAX_PER_KEY = 200  # ограничим рост файла


def _load() -> Dict[str, Dict[str, Dict[str, str | int]]]:
    if not _HISTORY_PATH.exists():
        return {}
    try:
        data = json.loads(_HISTORY_PATH.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except Exception:
        return {}
    return {}


def _save(data: Dict[str, Dict[str, Dict[str, str | int]]]) -> None:
    try:
        _HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        _HISTORY_PATH.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception as exc:
        logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)


def record_use(key: str, label: str) -> None:
    label_norm = normalize_for_search(label) or ""
    if not label_norm:
        return
    data = _load()
    by_key = data.setdefault(key, {})
    entry = by_key.get(label_norm, {"label": label, "count": 0, "last": 0})
    entry["label"] = label  # сохраняем оригинальную форму последнего выбора
    entry["count"] = int(entry.get("count", 0)) + 1
    entry["last"] = int(time.time())
    by_key[label_norm] = entry
    # trim if too many
    if len(by_key) > _MAX_PER_KEY:
        items = sorted(
            by_key.items(),
            key=lambda kv: (kv[1].get("count", 0), kv[1].get("last", 0)),
            reverse=True,
        )[:_MAX_PER_KEY]
        data[key] = {k: v for k, v in items}
    _save(data)


def get_recent(key: str, prefix: str | None = None, limit: int = 10) -> List[str]:
    data = _load()
    by_key = data.get(key, {})
    items = list(by_key.values())
    if prefix:
        pnorm = normalize_for_search(prefix) or ""
        items = [
            e
            for e in items
            if (normalize_for_search(e.get("label", "")) or "").startswith(pnorm)
        ]
    items.sort(
        key=lambda e: (int(e.get("count", 0)), int(e.get("last", 0))), reverse=True
    )
    return [str(e.get("label", "")) for e in items[:limit]]


def delete_entry(key: str, label: str) -> None:
    """Удаляет один элемент истории по ключу и текстовой метке (без учета регистра)."""
    label_norm = normalize_for_search(label) or ""
    if not label_norm:
        return
    data = _load()
    by_key = data.get(key)
    if not by_key:
        return
    if label_norm in by_key:
        try:
            del by_key[label_norm]
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)
        _save(data)


def purge_missing(key: str, valid_norms: set[str]) -> int:
    """Удаляет из истории все записи, которых нет в наборе существующих значений (valid_norms).

    valid_norms — нормализованные строки (normalize_for_search) актуальных значений из БД.
    Возвращает количество удаленных записей.
    """
    data = _load()
    by_key = data.get(key)
    if not by_key:
        return 0
    to_delete = [norm for norm in list(by_key.keys()) if norm not in valid_norms]
    for norm in to_delete:
        try:
            del by_key[norm]
        except Exception as exc:
            logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)
    if to_delete:
        _save(data)
    return len(to_delete)
