
import csv
from collections.abc import Iterator, Sequence
from pathlib import Path


def iter_csv_rows(
    path: str | Path,
    required_columns: Sequence[str] = (),
) -> Iterator[dict[str, str]]:
    """Yield CSV rows after validating the header."""
    csv_path = Path(path)

    with csv_path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        if reader.fieldnames is None:
            raise ValueError(f"CSV has no header: {csv_path}")

        missing_columns = [
            column
            for column in required_columns
            if column not in reader.fieldnames
        ]

        if missing_columns:
            missing = ", ".join(missing_columns)
            raise ValueError(
                f"Missing required columns in {csv_path}: {missing}"
            )

        yield from reader


def count_csv_rows(
    path: str | Path,
    required_columns: Sequence[str] = (),
) -> int:
    """Count data rows while validating the CSV header."""
    return sum(
        1
        for _ in iter_csv_rows(path, required_columns)
    )


def validate_unique_column(
    path: str | Path,
    column: str,
) -> None:
    """Raise ValueError if a CSV column contains duplicate values."""
    seen = set()

    for row_number, row in enumerate(
        iter_csv_rows(path, [column]),
        start=2,
    ):
        value = row[column]

        if value in seen:
            raise ValueError(
                f"Duplicate value {value!r} in column "
                f"{column!r} at CSV row {row_number}: {path}"
            )

        seen.add(value)


def validate_foreign_key(
    child_path: str | Path,
    child_column: str,
    parent_path: str | Path,
    parent_column: str,
) -> None:
    """Raise ValueError if child values are missing from the parent column."""
    parent_values = {
        row[parent_column]
        for row in iter_csv_rows(parent_path, [parent_column])
    }

    for row_number, row in enumerate(
        iter_csv_rows(child_path, [child_column]),
        start=2,
    ):
        value = row[child_column]

        if value not in parent_values:
            raise ValueError(
                f"Foreign-key value {value!r} in column "
                f"{child_column!r} at CSV row {row_number} "
                f"does not exist in {parent_path} column "
                f"{parent_column!r}"
            )


def validate_optional_foreign_key(
    child_path: str | Path,
    child_column: str,
    parent_path: str | Path,
    parent_column: str,
    allowed_unmatched: set[str] | None = None,
) -> list[str]:
    """Validate optional references and return allowed unmatched values."""
    allowed = allowed_unmatched or set()

    parent_values = {
        row[parent_column].strip()
        for row in iter_csv_rows(parent_path, [parent_column])
        if row[parent_column].strip()
    }

    unmatched_allowed = set()

    for row_number, row in enumerate(
        iter_csv_rows(child_path, [child_column]),
        start=2,
    ):
        value = row[child_column].strip()

        if not value or value in parent_values:
            continue

        if value in allowed:
            unmatched_allowed.add(value)
            continue

        raise ValueError(
            f"Unexpected foreign-key value {value!r} in column "
            f"{child_column!r} at CSV row {row_number}; "
            f"not found in {parent_path} column {parent_column!r}"
        )

    return sorted(unmatched_allowed)


def validate_datetime_column(
    path: str | Path,
    column: str,
    allow_blank: bool = False,
) -> None:
    """Validate ISO-format timestamps, optionally permitting blank values."""
    from datetime import datetime

    for row_number, row in enumerate(
        iter_csv_rows(path, [column]),
        start=2,
    ):
        value = (row[column] or "").strip()

        if not value:
            if allow_blank:
                continue

            raise ValueError(
                f"Blank timestamp in column {column!r} "
                f"at CSV row {row_number}: {path}"
            )

        try:
            datetime.fromisoformat(value)
        except ValueError as error:
            raise ValueError(
                f"Invalid timestamp {value!r} in column "
                f"{column!r} at CSV row {row_number}: {path}"
            ) from error
