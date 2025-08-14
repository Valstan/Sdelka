from __future__ import annotations

import subprocess
import datetime as dt
from pathlib import Path


def _run_git(args: list[str]) -> str | None:
	try:
		res = subprocess.run(["git", *args], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, cwd=str(Path(__file__).resolve().parents[1])),
		r = res[0]
		if r.returncode != 0:
			return None
		out = (r.stdout or "").strip()
		return out
	except Exception:
		return None


def _latest_commit_ts() -> int | None:
	out = _run_git(["log", "-1", "--format=%ct"])  # unix epoch seconds
	if not out:
		return None
	try:
		return int(out)
	except Exception:
		return None


def _count_commits_in_month(year: int, month: int) -> int | None:
	# диапазон: [first_day, first_day_next)
	first = dt.datetime(year, month, 1, 0, 0, 0)
	if month == 12:
		next_first = dt.datetime(year + 1, 1, 1, 0, 0, 0)
	else:
		next_first = dt.datetime(year, month + 1, 1, 0, 0, 0)
	since = first.strftime("%Y-%m-%d 00:00:00")
	until = next_first.strftime("%Y-%m-%d 00:00:00")
	out = _run_git(["log", f"--since={since}", f"--until={until}", "--pretty=%H"]) or ""
	lines = [ln for ln in out.splitlines() if ln.strip()]
	return len(lines)


def get_version() -> str:
	"""Возвращает строку версии вида 2.Y.M.COUNT, где
	Y — последняя цифра года последнего коммита,
	M — номер месяца последнего коммита,
	COUNT — число коммитов в этом месяце (с начала месяца).
	"""
	ts = _latest_commit_ts()
	if ts is not None:
		dt_last = dt.datetime.fromtimestamp(ts)
		year = dt_last.year
		month = dt_last.month
		count = _count_commits_in_month(year, month) or 1
		return f"2.{year % 10}.{month}.{count}"
	# fallback — нет git: используем текущую дату и счётчик 1
	now = dt.datetime.now()
	return f"2.{now.year % 10}.{now.month}.1"