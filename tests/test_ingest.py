import tempfile
import unittest
from pathlib import Path

from src.ingest import count_csv_rows, iter_csv_rows


class TestIngest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.csv_path = Path(self.temp_dir.name) / "sample.csv"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_reads_csv_rows(self):
        self.csv_path.write_text(
            "id,name\n1,Alice\n2,Bob\n",
            encoding="utf-8",
        )

        rows = list(
            iter_csv_rows(self.csv_path, ["id", "name"])
        )

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["name"], "Alice")

    def test_counts_csv_rows(self):
        self.csv_path.write_text(
            "id,name\n1,Alice\n2,Bob\n",
            encoding="utf-8",
        )

        self.assertEqual(count_csv_rows(self.csv_path), 2)

    def test_rejects_missing_required_column(self):
        self.csv_path.write_text(
            "id,name\n1,Alice\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(
            ValueError,
            "Missing required columns",
        ):
            count_csv_rows(self.csv_path, ["email"])


if __name__ == "__main__":
    unittest.main()