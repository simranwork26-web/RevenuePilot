import tempfile
import unittest
from pathlib import Path

from src.ingest import validate_datetime_column


class TestTimestampValidation(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.csv_path = Path(self.temp_dir.name) / "timestamps.csv"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_accepts_valid_timestamps(self):
        self.csv_path.write_text(
            "timestamp\n2018-01-01T10:30:00\n",
            encoding="utf-8",
        )
        validate_datetime_column(self.csv_path, "timestamp")

    def test_allows_blank_when_configured(self):
        self.csv_path.write_text(
            "timestamp\n \n2018-01-01T10:30:00\n",
            encoding="utf-8",
        )
        validate_datetime_column(
            self.csv_path,
            "timestamp",
            allow_blank=True,
        )

    def test_rejects_blank_when_required(self):
        self.csv_path.write_text(
            "timestamp\n \n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "Blank timestamp"):
            validate_datetime_column(self.csv_path, "timestamp")

    def test_rejects_invalid_timestamp(self):
        self.csv_path.write_text(
            "timestamp\nnot-a-date\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "Invalid timestamp"):
            validate_datetime_column(self.csv_path, "timestamp")


if __name__ == "__main__":
    unittest.main()
