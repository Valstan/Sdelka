from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from pathlib import Path

# ВЕРСИОНИРОВАНИЕ БЕЗ ЗАВИСИМОСТИ ОТ GIT
# Формат: 2.<последняя цифра года>.<месяц>.<счётчик изменений в текущем месяце>
# Счётчик автоматически увеличивается при изменении отпечатка исходников (.py)
# и сбрасывается при смене месяца.


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


def get_version() -> str:
	"""Возвращает строку версии вида 2.Y.M.COUNT, где
	Y — последняя цифра текущего года,
	M — номер текущего месяца (1-12),
	COUNT — счётчик изменений исходников в текущем месяце.
	"""
	now = dt.datetime.now()
	year = now.year
	month = now.month
	last_digit = year % 10
	fp = _compute_sources_fingerprint()

	state = _load_state()
	st_year = int(state.get("year", 0) or 0)
	st_month = int(state.get("month", 0) or 0)
	st_counter = int(state.get("counter", 0) or 0)
	st_fp = str(state.get("fingerprint", "") or "")

	# Смена месяца — сброс счётчика
	if st_year != year or st_month != month:
		st_counter = 0
		st_fp = ""

	# Если отпечаток изменился — это новое изменение
	if fp != st_fp:
		st_counter += 1
		st_fp = fp

	# Сохраняем состояние
	state.update({
		"year": year,
		"month": month,
		"counter": st_counter,
		"fingerprint": st_fp,
	})
	_save_state(state)

	return f"2.{last_digit}.{month}.{st_counter or 1}"