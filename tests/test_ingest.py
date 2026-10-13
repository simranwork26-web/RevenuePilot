import tempfile
import unittest
from pathlib import Path

from src.ingest import (
    count_csv_rows,
    iter_csv_rows,
    validate_unique_column,
    validate_foreign_key,
)


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

    def test_detects_duplicate_order_ids(self):
        self.csv_path.write_text(
            "order_id,status\n"
            "order_1,delivered\n"
            "order_1,canceled\n",
            encoding="utf-8",
        )

        rows = list(iter_csv_rows(self.csv_path))
        order_ids = [row["order_id"] for row in rows]

        self.assertNotEqual(
            len(order_ids),
            len(set(order_ids)),
        )


    def test_unique_column_passes(self):
        self.csv_path.write_text(
            "order_id,status\n"
            "order_1,delivered\n"
            "order_2,canceled\n",
            encoding="utf-8",
        )

        validate_unique_column(self.csv_path, "order_id")

    def test_unique_column_rejects_duplicates(self):
        self.csv_path.write_text(
            "order_id,status\n"
            "order_1,delivered\n"
            "order_1,canceled\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ValueError, "Duplicate value"):
            validate_unique_column(self.csv_path, "order_id")



    def test_foreign_key_accepts_valid_references(self):
        parent = Path(self.temp_dir.name) / "parents.csv"
        parent.write_text(
            "id\nA\nB\n",
            encoding="utf-8",
        )
        self.csv_path.write_text(
            "parent_id\nA\nB\n",
            encoding="utf-8",
        )

        validate_foreign_key(
            self.csv_path, "parent_id", parent, "id"
        )

    def test_foreign_key_rejects_missing_reference(self):
        parent = Path(self.temp_dir.name) / "parents.csv"
        parent.write_text(
            "id\nA\nB\n",
            encoding="utf-8",
        )
        self.csv_path.write_text(
            "parent_id\nA\nMISSING\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ValueError, "Foreign-key value"):
            validate_foreign_key(
                self.csv_path, "parent_id", parent, "id"
            )


if __name__ == "__main__":
    unittest.main()
