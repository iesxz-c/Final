"""Phase 2A tests: deterministic subset selection (no dataset needed)."""

import unittest

from src.pipeline import select_subset as sel


def make_records(categories: dict) -> list:
    records = []
    for category, n in categories.items():
        source = "normal" if category == "Normal" else "anomaly"
        for i in range(n):
            vid = f"{source}/{category}/{category}{i:03d}_x264.mp4"
            records.append(
                {
                    "video_id": vid,
                    "source_type": source,
                    "category": category,
                    "dataset_root": "/root",
                    "path": f"{category}/{category}{i:03d}_x264.mp4",
                    "duration_seconds": 10.0,
                    "fps": 30.0,
                    "width": 320,
                    "height": 240,
                    "frame_count": 300,
                    "file_size_bytes": 1000,
                    "format": "mp4",
                }
            )
    return records


SELECTION = [
    {"category": "Fighting", "count": 5},
    {"category": "Assault", "count": 5},
    {"category": "Robbery", "count": 5},
    {"category": "Shooting", "count": 5},
    {"category": "Shoplifting", "count": 5},
    {"category": "Stealing", "count": 5},
    {"category": "Vandalism", "count": 5},
    {"category": "Normal", "count": 5},
]


class SelectSubsetTest(unittest.TestCase):
    def setUp(self):
        cats = {s["category"]: 8 for s in SELECTION}
        self.records = make_records(cats)

    def test_selects_exactly_40_with_category_counts(self):
        selected = sel.select_subset(self.records, SELECTION)
        entries = sel.to_subset_entries(selected)
        counts = sel.validate_subset(entries, SELECTION)
        self.assertEqual(len(entries), 40)
        self.assertEqual(counts, {s["category"]: 5 for s in SELECTION})

    def test_selection_is_deterministic(self):
        first = sel.select_subset(self.records, SELECTION)
        shuffled = list(reversed(self.records))
        second = sel.select_subset(shuffled, SELECTION)
        self.assertEqual(
            [r["video_id"] for r in first], [r["video_id"] for r in second]
        )

    def test_takes_first_n_by_video_id(self):
        selected = sel.select_subset(self.records, [{"category": "Fighting", "count": 5}])
        ids = [r["video_id"] for r in selected]
        self.assertEqual(ids, sorted(ids))
        self.assertTrue(all("Fighting000" in v or "Fighting001" in v or
                            "Fighting002" in v or "Fighting003" in v or
                            "Fighting004" in v for v in ids))

    def test_too_few_candidates_raises(self):
        records = make_records({"Fighting": 3})
        with self.assertRaises(ValueError):
            sel.select_subset(records, [{"category": "Fighting", "count": 5}])

    def test_entries_use_ground_truth_naming(self):
        entries = sel.to_subset_entries(
            sel.select_subset(self.records, SELECTION[:1])
        )
        self.assertEqual(len(entries), 5)
        for entry in entries:
            self.assertEqual(entry["ground_truth_category"], "Fighting")
            self.assertNotIn("activity", entry)
            self.assertIn("video_id", entry)
            self.assertIn("path", entry)

    def test_validate_rejects_wrong_counts(self):
        entries = sel.to_subset_entries(
            sel.select_subset(self.records, SELECTION)
        )[:39]
        with self.assertRaises(ValueError):
            sel.validate_subset(entries, SELECTION)

    def test_validate_rejects_duplicates(self):
        entries = sel.to_subset_entries(
            sel.select_subset(self.records, SELECTION)
        )
        entries.append(dict(entries[0]))
        with self.assertRaises(ValueError):
            sel.validate_subset(entries, SELECTION)


if __name__ == "__main__":
    unittest.main()