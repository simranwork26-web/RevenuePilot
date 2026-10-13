import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.validate_dataset import validate_dataset


class TestValidateDataset(unittest.TestCase):
    def test_missing_dataset_file_fails_validation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temporary_root = Path(temp_dir)

            with (
                patch("src.validate_dataset.RAW_DATA_DIR", temporary_root),
                patch("builtins.print") as mock_print,
                patch(
                    "src.validate_dataset.DATASET_MANIFEST",
                    {"missing.csv": {"expected_rows": 1, "required_columns": []}},
                ),
            ):
                result = validate_dataset()

            self.assertFalse(result)
            printed_text = " ".join(
                str(call) for call in mock_print.call_args_list
            )
            self.assertIn("Missing file", printed_text)

    def test_row_count_mismatch_fails_validation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temporary_root = Path(temp_dir)
            dataset_path = temporary_root / "sample.csv"
            dataset_path.write_text("id\n1\n2\n", encoding="utf-8")

            manifest = {
                "sample.csv": {
                    "expected_rows": 3,
                    "required_columns": ["id"],
                }
            }

            with (
                patch("src.validate_dataset.RAW_DATA_DIR", temporary_root),
                patch("src.validate_dataset.DATASET_MANIFEST", manifest),
                patch("builtins.print") as mock_print,
            ):
                result = validate_dataset()

            self.assertFalse(result)
            printed_text = " ".join(
                str(call) for call in mock_print.call_args_list
            )
            self.assertIn("expected 3 rows, found 2", printed_text)


if __name__ == "__main__":
    unittest.main()
