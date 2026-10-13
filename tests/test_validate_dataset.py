import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.validate_dataset import validate_dataset


class TestValidateDataset(unittest.TestCase):
    def test_missing_dataset_file_fails_validation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temporary_root = Path(temp_dir)

            with patch(
                "src.validate_dataset.RAW_DATA_DIR",
                temporary_root,
            ):
                with patch(
                    "builtins.print"
                ) as mock_print:
                    result = validate_dataset()

            self.assertFalse(result)
            printed_text = " ".join(
                str(call) for call in mock_print.call_args_list
            )
            self.assertIn("Missing file", printed_text)


if __name__ == "__main__":
    unittest.main()
