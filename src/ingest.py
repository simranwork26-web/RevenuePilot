
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
