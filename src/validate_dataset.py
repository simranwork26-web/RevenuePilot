from src.dataset_manifest import DATASET_MANIFEST, RAW_DATA_DIR
from src.ingest import (
    count_csv_rows,
    validate_foreign_key,
    validate_optional_foreign_key,
    validate_unique_column,
)


def validate_dataset() -> bool:
    """Validate source files, schemas, keys, row counts, and relationships."""
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
            continue

        dataset_failed = False

        for column in specification.get("unique_columns", []):
            try:
                validate_unique_column(path, column)
            except (OSError, ValueError) as error:
                errors.append(f"{filename}: {error}")
                dataset_failed = True

        if not dataset_failed:
            print(f"PASS: {filename} ({actual_rows:,} rows)")

    for filename, specification in DATASET_MANIFEST.items():
        child_path = RAW_DATA_DIR / filename

        if not child_path.is_file():
            continue

        for relationship in specification.get("foreign_keys", []):
            parent_path = RAW_DATA_DIR / relationship["parent_file"]

            if not parent_path.is_file():
                errors.append(
                    f"{filename}: missing parent file "
                    f"{relationship['parent_file']}"
                )
                continue

            try:
                validate_foreign_key(
                    child_path,
                    relationship["column"],
                    parent_path,
                    relationship["parent_column"],
                )
                print(
                    f"PASS: {filename}.{relationship['column']} -> "
                    f"{relationship['parent_file']}."
                    f"{relationship['parent_column']}"
                )
            except (OSError, ValueError) as error:
                errors.append(f"{filename}: {error}")

        for relationship in specification.get("optional_foreign_keys", []):
            parent_path = RAW_DATA_DIR / relationship["parent_file"]

            if not parent_path.is_file():
                errors.append(
                    f"{filename}: missing parent file "
                    f"{relationship['parent_file']}"
                )
                continue

            try:
                allowed_unmatched = validate_optional_foreign_key(
                    child_path,
                    relationship["column"],
                    parent_path,
                    relationship["parent_column"],
                    set(relationship.get("allowed_unmatched", [])),
                )
                print(
                    f"PASS: {filename}.{relationship['column']} -> "
                    f"{relationship['parent_file']}."
                    f"{relationship['parent_column']}"
                )

                if allowed_unmatched:
                    print(
                        "KNOWN UNTRANSLATED CATEGORIES:",
                        ", ".join(allowed_unmatched),
                    )
            except (OSError, ValueError) as error:
                errors.append(f"{filename}: {error}")

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
