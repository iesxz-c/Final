"""Tests for safe stdlib `.env` loading and its Phase 3C wiring.

Uses synthetic values only; never touches the real repo-root `.env`.
"""

import os
import unittest
from pathlib import Path
from unittest import mock

from src import env_file as D


def _write_tmp(path, text):
    Path(path).write_text(text, encoding="utf-8")


class ParseTest(unittest.TestCase):
    def test_basic_and_spacing(self):
        self.assertEqual(D.parse_env_text("A=1\nB = two \n"), {"A": "1", "B": "two"})

    def test_comments_and_blanks(self):
        text = "# leading\n\nA=1 # trailing\n   # indented\nB=2\n"
        self.assertEqual(D.parse_env_text(text), {"A": "1", "B": "2"})

    def test_quotes_and_export(self):
        text = 'A="x y"\nB=\'a#b\'\nexport C=3\nD="esc \\"q\\" end"\n'
        parsed = D.parse_env_text(text)
        self.assertEqual(parsed["A"], "x y")
        self.assertEqual(parsed["B"], "a#b")
        self.assertEqual(parsed["C"], "3")
        self.assertEqual(parsed["D"], 'esc "q" end')

    def test_invalid_lines_ignored(self):
        text = "no-equals\n9BAD=x\nBAD-KEY=y\n=novalue\nGOOD=ok\nGOOD=overridden-in-file\n"
        self.assertEqual(D.parse_env_text(text), {"GOOD": "overridden-in-file"})


class LoadTest(unittest.TestCase):
    def setUp(self):
        self._dir = Path(os.environ.get("TEMP", "/tmp")) / "opencode_env_test"
        self._dir.mkdir(parents=True, exist_ok=True)
        self._saved = dict(os.environ)

    def tearDown(self):
        for child in self._dir.glob("*"):
            child.unlink()
        self._dir.rmdir()
        os.environ.clear()
        os.environ.update(self._saved)

    def _tmp(self, name, text):
        path = self._dir / name
        _write_tmp(path, text)
        return path

    def test_sets_missing_only(self):
        os.environ.pop("EFT_A", None)
        os.environ["EFT_B"] = "real-env-wins"
        loaded = D.load_env_file(self._tmp("t.env", "EFT_A=from-file\nEFT_B=from-file\n"))
        self.assertEqual(os.environ["EFT_A"], "from-file")
        self.assertEqual(os.environ["EFT_B"], "real-env-wins")
        self.assertEqual(loaded, {"EFT_A": "from-file"})

    def test_missing_file_ignored(self):
        self.assertEqual(D.load_env_file(self._dir / "absent.env"), {})

    def test_default_path_constant(self):
        self.assertEqual(D.DEFAULT_ENV_PATH.name, ".env")
        self.assertTrue((D.DEFAULT_ENV_PATH.parent / "src" / "env_file.py").exists())

    def test_oversize_file_ignored(self):
        path = self._tmp("big.env", "EFT_BIG=1\n")
        with mock.patch.object(D, "MAX_ENV_FILE_BYTES", 4):
            self.assertEqual(D.load_env_file(path), {})
        self.assertNotIn("EFT_BIG", os.environ)


class WiringTest(unittest.TestCase):
    def setUp(self):
        self._saved = dict(os.environ)
        os.environ.pop("MODEL_API_KEY", None)
        self._dir = Path(os.environ.get("TEMP", "/tmp")) / "opencode_env_wire"
        self._dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        for child in self._dir.glob("*"):
            child.unlink()
        self._dir.rmdir()
        os.environ.clear()
        os.environ.update(self._saved)

    def test_client_reads_env_file(self):
        from src.agents.llm_client import MetaDirectClient

        _write_tmp(self._dir / "w.env", "MODEL_API_KEY=synthetic-test-key\n")
        D.load_env_file(self._dir / "w.env")
        client = MetaDirectClient(model="m")
        self.assertNotIn("synthetic-test-key", repr(client))

    def test_planner_settings_read_env_file(self):
        from src.agents.query_planner import MODEL_ENV, load_llm_settings

        os.environ.pop(MODEL_ENV, None)
        _write_tmp(self._dir / "s.env", f"{MODEL_ENV}=synthetic/test-model\n")
        D.load_env_file(self._dir / "s.env")
        with mock.patch("src.settings.load_config", return_value={}):
            settings = load_llm_settings()
        self.assertEqual(settings["model"], "synthetic/test-model")

    def test_frozen_model_selected_and_pinned(self):
        from src.agents.llm_client import DEFAULT_MODEL, LLMError
        from src.agents.query_planner import MODEL_ENV, create_client, load_llm_settings

        self.assertEqual(DEFAULT_MODEL, "muse-spark-1.3-contributor")
        os.environ["CCTV_LLM_PROVIDER"] = "meta"
        os.environ.pop(MODEL_ENV, None)
        with mock.patch("src.agents.query_planner.load_env_file",
                        lambda path=None: {}), \
             mock.patch("src.settings.load_config", return_value={}):
            settings = load_llm_settings()
        self.assertEqual(settings["model"], "muse-spark-1.3-contributor")
        client = create_client(settings, api_key="synthetic-test-key")
        self.assertEqual(client.model, "muse-spark-1.3-contributor")
        os.environ[MODEL_ENV] = "someone-else/model"
        with mock.patch("src.agents.query_planner.load_env_file",
                        lambda path=None: {}), \
             mock.patch("src.settings.load_config", return_value={}):
            settings = load_llm_settings()
        with self.assertRaises(LLMError):
            create_client(settings, api_key="synthetic-test-key")

    def test_official_default_model_is_muse(self):
        import yaml

        with (D.PROJECT_ROOT / "config" / "config.example.yaml").open(
                "r", encoding="utf-8") as fh:
            config = yaml.safe_load(fh)
        self.assertEqual(config["llm"]["provider"], "meta")
        self.assertEqual(config["llm"]["model"], "muse-spark-1.3-contributor")

    def test_example_and_ignore_rules(self):
        import subprocess

        root = D.PROJECT_ROOT
        example = (root / ".env.example").read_text(encoding="utf-8")
        self.assertIn("MODEL_API_KEY=", example)
        self.assertNotIn("OPENROUTER", example)
        self.assertNotIn("openrouter.ai", example)
        self.assertNotIn("sk-", example)
        ignored = subprocess.run(
            ["git", "check-ignore", ".env", ".env.example"], cwd=root,
            capture_output=True, text=True).stdout.split()
        self.assertIn(".env", ignored)
        self.assertNotIn(".env.example", ignored)


if __name__ == "__main__":
    unittest.main()
