from datetime import date, datetime
from decimal import Decimal

import pytest

from src.load_postgres import parse_value, read_dataset


def test_blank_values_become_none():
    assert parse_value("item_value", "", {"decimals": {"item_value"}}) is None
    assert parse_value("item_value", "   ", {"decimals": {"item_value"}}) is None
    assert parse_value("item_value", None, {"decimals": {"item_value"}}) is None


def test_integer_values_are_parsed():
    config = {"integers": {"item_count"}}

    assert parse_value("item_count", "12", config) == 12
    assert parse_value("item_count", "12.0", config) == 12


@pytest.mark.parametrize("value", ["1.5", "abc", "NaN", "Infinity"])
def test_invalid_integer_values_are_rejected(value):
    with pytest.raises(ValueError):
        parse_value("item_count", value, {"integers": {"item_count"}})


def test_decimal_values_preserve_precision():
    result = parse_value(
        "high_value_threshold",
        "499.1460000000002",
        {"decimals": {"high_value_threshold"}},
    )

    assert result == Decimal("499.1460000000002")


@pytest.mark.parametrize("value", ["NaN", "Infinity", "-Infinity"])
def test_non_finite_decimals_are_rejected(value):
    with pytest.raises(ValueError):
        parse_value("item_value", value, {"decimals": {"item_value"}})


def test_timestamp_and_date_values_are_parsed():
    config = {
        "dates": {
            "purchase_timestamp": "timestamp",
            "reference_date": "date",
        }
    }

    assert parse_value(
        "purchase_timestamp", "2018-10-17T12:30:00", config
    ) == datetime(2018, 10, 17, 12, 30)

    assert parse_value(
        "reference_date", "2018-10-18", config
    ) == date(2018, 10, 18)


def test_boolean_values_are_parsed_case_insensitively():
    config = {"booleans": {"low_volume_month"}}

    assert parse_value("low_volume_month", "true", config) is True
    assert parse_value("low_volume_month", "FALSE", config) is False


@pytest.mark.parametrize("value", ["yes", "1", "maybe"])
def test_invalid_boolean_values_are_rejected(value):
    with pytest.raises(ValueError):
        parse_value("low_volume_month", value, {"booleans": {"low_volume_month"}})


def test_text_values_are_trimmed():
    assert parse_value("segment", "  Repeat  ", {}) == "Repeat"


def test_read_dataset_rejects_unexpected_columns(tmp_path, monkeypatch):
    import src.load_postgres as loader

    test_file = tmp_path / "sample.csv"
    test_file.write_text("wrong_column\nvalue\n", encoding="utf-8")

    monkeypatch.setattr(loader, "DATA_DIR", tmp_path)

    config = {
        "file": "sample.csv",
        "columns": ["expected_column"],
    }

    with pytest.raises(ValueError, match="Unexpected columns"):
        read_dataset("sample", config)


def test_read_dataset_converts_rows_and_preserves_missing_values(
    tmp_path, monkeypatch
):
    import src.load_postgres as loader

    test_file = tmp_path / "sample.csv"
    test_file.write_text(
        "name,item_count,item_value\n"
        "  Repeat  ,2,12.50\n"
        "One-time,,\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(loader, "DATA_DIR", tmp_path)

    config = {
        "file": "sample.csv",
        "columns": ["name", "item_count", "item_value"],
        "integers": {"item_count"},
        "decimals": {"item_value"},
    }

    rows = read_dataset("sample", config)

    assert rows == [
        ("Repeat", 2, Decimal("12.50")),
        ("One-time", None, None),
    ]


def test_read_dataset_reports_invalid_csv_row(tmp_path, monkeypatch):
    import src.load_postgres as loader

    test_file = tmp_path / "sample.csv"
    test_file.write_text(
        "item_count\n"
        "2\n"
        "invalid\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(loader, "DATA_DIR", tmp_path)

    config = {
        "file": "sample.csv",
        "columns": ["item_count"],
        "integers": {"item_count"},
    }

    with pytest.raises(ValueError, match="CSV row 3"):
        read_dataset("sample", config)
