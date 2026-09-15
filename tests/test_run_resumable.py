"""Resumable UCF runner tests: checkpointing, resume, merge, streaming. No
inference, no GPU, no real subprocess - the extract CLI invocation is faked."""

import importlib.util
import json
import subprocess
import sys
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock
from unittest import mock

_SPEC = importlib.util.spec_from_file_location(
    "run_resumable_ucf",
    Path(__file__).resolve().parent.parent / "scripts" / "run_resumable_ucf.py")
R = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(R)


def _manifest(path: Path, n: int, prefix="anomaly/Cat") -> Path:
    videos = [{"video_id": f"{prefix}/v{i:03d}.mp4", "source_type": "anomaly",
               "ground_truth_category": "Cat", "dataset_root": "/data",
               "path": f"Cat/v{i:03d}.mp4"}
              for i in range(n)]
    path.write_text(json.dumps({"videos": videos}), encoding="utf-8")
    return path


def _fake_invoke_factory(seen=None, fail_videos=(), empty_for=()):
    seen = seen if seen is not None else []
    fail_videos = set(fail_videos)

    def _invoke(batch_manifest: Path, batch_dir: Path, device: str) -> int:
        entries = json.loads(Path(batch_manifest).read_text(encoding="utf-8"))["videos"]
        seen.extend(v["video_id"] for v in entries)
        ok = [v for v in entries if v["video_id"] not in fail_videos]
        batch_dir = Path(batch_dir)
        batch_dir.mkdir(parents=True, exist_ok=True)
        (batch_dir / "videos.json").write_text(json.dumps(ok), encoding="utf-8")
        events = []
        for v in ok:
            if v["video_id"] in empty_for:
                continue
            events.append({"observation_id": v["video_id"] + ":e0",
                           "video_id": v["video_id"], "start_time": 0.0})
        (batch_dir / "ucf_events.json").write_text(json.dumps(events), encoding="utf-8")
        (batch_dir / "manifest.json").write_text(json.dumps(
            {"videos_processed": len(ok),
             "failures": [{"video_id": v} for v in fail_videos
                          if v in {e["video_id"] for e in entries}]}),
            encoding="utf-8")
        return 0 if not fail_videos else 1

    return _invoke


class ResumableTest(unittest.TestCase):
    def test_fresh_run(self):
        with TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            manifest = _manifest(tmp / "in.json", 5)
            out = tmp / "out"
            code = R.run_batches(manifest, out, "cpu", 2, None,
                                 _fake_invoke_factory())
            self.assertEqual(code, 0)
            state = json.loads((out / "state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["total_videos"], 5)
            self.assertEqual(len(state["completed_video_ids"]), 5)
            self.assertEqual(state["batches_completed"], 3)
            for key in ("schema_version", "input_manifest", "completed_video_ids",
                        "failed_video_ids", "batches_completed", "last_updated"):
                self.assertIn(key, state)

    def test_resume_after_completed_batch(self):
        with TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            manifest = _manifest(tmp / "in.json", 5)
            out = tmp / "out"
            seen = []
            fake = _fake_invoke_factory(seen)
            self.assertEqual(R.run_batches(manifest, out, "cpu", 2, 1, fake), 0)
            self.assertEqual(R.run_batches(manifest, out, "cpu", 2, None, fake), 0)
            state = json.loads((out / "state.json").read_text(encoding="utf-8"))
            self.assertEqual(len(state["completed_video_ids"]), 5)
            self.assertEqual(state["batches_completed"], 3)

    def test_no_duplicate_processing(self):
        with TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            manifest = _manifest(tmp / "in.json", 5)
            out = tmp / "out"
            seen = []
            fake = _fake_invoke_factory(seen)
            R.run_batches(manifest, out, "cpu", 2, 1, fake)
            R.run_batches(manifest, out, "cpu", 2, None, fake)
            self.assertEqual(len(seen), len(set(seen)))
            self.assertEqual(len(seen), 5)

    def test_partial_batch_failure(self):
        with TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            manifest = _manifest(tmp / "in.json", 4)
            out = tmp / "out"
            victim = "anomaly/Cat/v002.mp4"
            code = R.run_batches(manifest, out, "cpu", 4, None,
                                 _fake_invoke_factory(fail_videos={victim}))
            self.assertEqual(code, 2)
            state = json.loads((out / "state.json").read_text(encoding="utf-8"))
            self.assertNotIn(victim, state["completed_video_ids"])
            self.assertEqual(len(state["completed_video_ids"]), 3)
            code = R.run_batches(manifest, out, "cpu", 4, None,
                                 _fake_invoke_factory())
            self.assertEqual(code, 0)
            state = json.loads((out / "state.json").read_text(encoding="utf-8"))
            self.assertEqual(len(state["completed_video_ids"]), 4)

    def test_existing_dirs_not_overwritten(self):
        with TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            manifest = _manifest(tmp / "in.json", 2)
            out = tmp / "out"
            R.run_batches(manifest, out, "cpu", 5, None, _fake_invoke_factory())
            before = {(p.name, p.read_bytes()) for p in sorted((out / "batch_001").iterdir())}
            self.assertEqual(R.run_batches(manifest, out, "cpu", 5, None,
                                           _fake_invoke_factory()), 0)
            after = {(p.name, p.read_bytes()) for p in sorted((out / "batch_001").iterdir())}
            self.assertEqual(before, after)

    def test_final_702_accounting_and_merge(self):
        with TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            manifest = _manifest(tmp / "in.json", 702)
            out = tmp / "out"
            self.assertEqual(R.run_batches(manifest, out, "cpu", 50, None,
                                           _fake_invoke_factory()), 0)
            merged = tmp / "merged"
            self.assertEqual(R.merge_batches(out, merged), 0)
            videos = json.loads((merged / "videos.json").read_text(encoding="utf-8"))
            events = json.loads((merged / "ucf_events.json").read_text(encoding="utf-8"))
            manifest_out = json.loads((merged / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(len(videos), 702)
            self.assertEqual(len(events), 702)
            self.assertEqual([v["video_id"] for v in videos],
                             sorted(v["video_id"] for v in videos))
            self.assertEqual(manifest_out["videos_failed"], 0)
            self.assertTrue((merged / "manifest.json").exists())

    def test_deterministic_ordering(self):
        with TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            states = []
            for run in ("a", "b"):
                manifest = _manifest(tmp / "in.json", 6)
                out = tmp / run
                R.run_batches(manifest, out, "cpu", 2, None, _fake_invoke_factory())
                state = json.loads((out / "state.json").read_text(encoding="utf-8"))
                state.pop("last_updated", None)
                states.append(state)
            self.assertEqual(states[0], states[1])

    def test_merge_rejects_duplicates(self):
        with TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            manifest = _manifest(tmp / "in.json", 2)
            out = tmp / "out"
            R.run_batches(manifest, out, "cpu", 5, None, _fake_invoke_factory())
            (out / "batch_002").mkdir()
            (out / "batch_002" / "videos.json").write_text(
                json.dumps([{"video_id": "anomaly/Cat/v000.mp4"}]), encoding="utf-8")
            (out / "batch_002" / "ucf_events.json").write_text("[]", encoding="utf-8")
            self.assertEqual(R.merge_batches(out, tmp / "merged"), 2)


STUB = (f"import sys, time; sys.stdout.write('out-1\\n'); sys.stdout.flush(); "
        f"sys.stderr.write('err-1\\n'); sys.stderr.flush(); "
        f"print('FIRST', flush=True); "
        f"time.sleep(1.2); print('SECOND', flush=True)")


class StreamingTest(unittest.TestCase):
    def _run_stub(self, script, exit_note=None):
        out, err = [], []
        start = time.monotonic()

        def emit_out(line):
            out.append((time.monotonic() - start, line))

        def emit_err(line):
            err.append((time.monotonic() - start, line))

        proc = subprocess.Popen(
            [sys.executable, "-u", "-c", script],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, bufsize=1)
        code = R._stream_and_wait(proc, emit_out, emit_err)
        return code, out, err

    def test_stdout_forwarded_while_running(self):
        code, out, err = self._run_stub(STUB)
        self.assertEqual(code, 0)
        first_at = next(t for t, line in out if "FIRST" in line)
        second_at = next(t for t, line in out if "SECOND" in line)
        self.assertGreater(second_at - first_at, 0.5)
        self.assertTrue(any("out-1" in line for _, line in out))
        self.assertTrue(any("err-1" in line for _, line in err))

    def test_stderr_forwarded(self):
        code, out, err = self._run_stub(
            "import sys; sys.stderr.write('boom\\n')")
        self.assertEqual(code, 0)
        self.assertEqual([line for _, line in err], ["boom\n"])
        self.assertEqual(out, [])

    def test_return_code_preserved(self):
        code, _, _ = self._run_stub("import sys; sys.exit(3)")
        self.assertEqual(code, 3)

    def test_invoke_uses_unbuffered_extract(self):
        seen = {}

        class _FakeProc:
            def wait(self):
                return 0

            @property
            def stdout(self):
                return _empty_stream()

            @property
            def stderr(self):
                return _empty_stream()

        def _empty_stream():
            import io
            return io.StringIO("")

        def _fake_popen(argv, **kwargs):
            seen["argv"] = argv
            return _FakeProc()

        with mock.patch.object(R.subprocess, "Popen", _fake_popen):
            code = R._invoke_extract(Path("in.json"), Path("out"), "cpu")
        self.assertEqual(code, 0)
        self.assertIn("-u", seen["argv"])
        self.assertIn("src.pipeline.extract_ucf_events", seen["argv"])


if __name__ == "__main__":
    unittest.main()
