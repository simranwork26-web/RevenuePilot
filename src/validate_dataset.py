from src.dataset_manifest import DATASET_MANIFEST, RAW_DATA_DIR
from src.ingest import count_csv_rows


def validate_dataset() -> bool:
    """Validate source files against the dataset manifest."""
    errors = []

    for filename, specification in DATASET_MANIFEST.items():
        path = RAW_DATA_DIR / filename

        if not path.is_file():
            errors.append(f"Missing file: {path}")
            continue

        try:
            actual_rows = count_csv_rows(
                path,
                specification["required_columns"],
            )
        except (OSError, ValueError) as error:
            errors.append(f"{filename}: {error}")
            continue

        expected_rows = specification["expected_rows"]

        if actual_rows != expected_rows:
            errors.append(
                f"{filename}: expected {expected_rows:,} rows, "
                f"found {actual_rows:,}"
            )
        else:
            print(f"PASS: {filename} ({actual_rows:,} rows)")

    if errors:
        print("\nVALIDATION FAILED")
        for error in errors:
            print(f"ERROR: {error}")
        return False

    print(f"\nVALIDATION PASSED: {len(DATASET_MANIFEST)} datasets")
    print(
        "TOTAL ROWS:",
        f"{sum(item['expected_rows'] for item in DATASET_MANIFEST.values()):,}",
    )
    return True


if __name__ == "__main__":
    raise SystemExit(0 if validate_dataset() else 1)