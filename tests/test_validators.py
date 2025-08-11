from __future__ import annotations

import pytest

from app.utils.validators import ValidationError, ensure_unique, parse_iso_date, require_non_negative, require_positive


def test_require_positive():
    require_positive(1, "x")
    with pytest.raises(ValidationError):
        require_positive(0, "x")


def test_require_non_negative():
    require_non_negative(0, "x")
    with pytest.raises(ValidationError):
        require_non_negative(-1, "x")


def test_parse_iso_date_ok():
    assert str(parse_iso_date("2024-05-10")) == "2024-05-10"


def test_parse_iso_date_bad():
    with pytest.raises(ValidationError):
        parse_iso_date("10-05-2024")


def test_ensure_unique():
    ensure_unique(["A", "B"], "ent", "field")
    with pytest.raises(ValidationError):
        ensure_unique(["A", "a"], "ent", "field")