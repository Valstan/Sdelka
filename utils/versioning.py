from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from pathlib import Path

# ВЕРСИОНИРОВАНИЕ БЕЗ ЗАВИСИМОСТИ ОТ GIT
# Формат: "3 сетевая от [дата последнего изменения]"
# Дата отображается в формате "18 августа 2025 года"
# Версия автоматически обновляется при изменении отпечатка исходников (.py)


def _project_root() -> Path:
	return Path(__file__).resolve().parents[1]


def _state_path() -> Path:
	root = _project_root()
	state_dir = root / "data"
	try:
		state_dir.mkdir(parents=True, exist_ok=True)
	except Exception:
		pass
	return state_dir / "version_state.json"


def _should_skip_dir(dirname: str) -> bool:
	name = dirname.lower()
	return name in {".git", ".idea", ".venv", "dist", "logs", "backups", "__pycache__"}


def _compute_sources_fingerprint() -> str:
	root = _project_root()
	md5 = hashlib.md5()
	# Проходим по дереву и учитываем только .py файлы
	for base, dirnames, filenames in os.walk(root):
		# Отфильтровать служебные каталоги
		dirnames[:] = [d for d in dirnames if not _should_skip_dir(d)]
		for fn in sorted(filenames):
			if not fn.lower().endswith(".py"):
				continue
			full = Path(base) / fn
			try:
				rel = str(full.relative_to(root)).replace("\\", "/")
				stat = full.stat()
				md5.update(rel.encode("utf-8", errors="ignore"))
				md5.update(str(stat.st_size).encode())
				md5.update(str(getattr(stat, "st_mtime_ns", int(stat.st_mtime * 1e9))).encode())
			except Exception:
				# Если какой-то файл внезапно исчез — пропускаем
				continue
	return md5.hexdigest()


def _load_state() -> dict:
	p = _state_path()
	if not p.exists():
		return {}
	try:
		return json.loads(p.read_text(encoding="utf-8")) or {}
	except Exception:
		return {}


def _save_state(state: dict) -> None:
	p = _state_path()
	try:
		p.write_text(json.dumps(state, ensure_ascii=False, indent=0), encoding="utf-8")
	except Exception:
		pass


def _get_month_name(month: int) -> str:
	"""Возвращает название месяца на русском языке в родительном падеже"""
	months = {
		1: "января", 2: "февраля", 3: "марта", 4: "апреля",
		5: "мая", 6: "июня", 7: "июля", 8: "августа",
		9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
	}
	return months.get(month, "неизвестного месяца")


def get_version() -> str:
	"""Фиксированная версия приложения."""
	return "3.9"