"""vector_store tests: text schema, index config, payload, manifest.

Synthetic records + fake embedder only - never the real corpus or model."""

import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from src.pipeline import vector_store as V


def _record(eid, obj=None, action=None, event=None):
    return {"evidence_id": eid, "video_id": "anomaly/X/x.mp4",
            "start_time": 0.0, "end_time": 2.0,
            "object_evidence": [{"class_name": obj, "confidence": 0.9}] if obj else [],
            "generic_action_evidence": [{"label": action, "confidence": 0.7,
                                         "top_k": [{"label": action + "-top",
                                                    "confidence": 0.1}]}]
            if action else [],
            "surveillance_event_evidence": [{"label": event, "confidence": 0.8,
                                             "top_k": []}] if event else [],
            "source_references": ["anomaly/X/x.mp4@t=0.0s-2.0s"],
            "anomaly_score": 0.5}


class FakeModel:
    def __init__(self, dim=384):
        self.dim = dim
        self.calls = []

    def encode(self, texts, batch_size=64, normalize_embeddings=True,
               show_progress_bar=False, convert_to_numpy=True):
        self.calls.append({"n": len(texts),
                           "normalized": normalize_embeddings})
        rng = np.random.default_rng(7)
        vectors = rng.normal(size=(len(texts), self.dim))
        vectors /= np.linalg.norm(vectors, axis=1, keepdims=True)
        return vectors


def _build(records, **kwargs):
    tmp = tempfile.TemporaryDirectory()
    kwargs.setdefault("batch_size", 2)
    manifest = V.build_index(records, Path(tmp.name) / "idx", model=FakeModel(),
                             **kwargs)
    return tmp, manifest


class TextSchemaTest(unittest.TestCase):
    def test_deterministic_sections(self):
        text = V.build_vector_text(_record("v:f0", obj="car", action="running",
                                           event="Fighting"))
        self.assertEqual(text, V.build_vector_text(_record("v:f0", obj="car",
                                                           action="running",
                                                           event="Fighting")))
        self.assertTrue(text.startswith("objects: car\n"))
        self.assertIn("\nactions: running, running-top\n", text)
        self.assertIn("\nevents: Fighting", text)

    def test_forbidden_fields_excluded(self):
        record = _record("sekrit-id:f0", obj="car")
        record["video_id"] = "anomaly/Sekrit/x.mp4"
        text = V.build_vector_text(record)
        for forbidden in ("sekrit-id", "Sekrit", "t=0.0s", "0.5", "0.9"):
            self.assertNotIn(forbidden, text)

    def test_sorted_unique_labels(self):
        record = _record("v:f0", obj="car")
        record["object_evidence"].append({"class_name": "car"})
        record["object_evidence"].append({"class_name": "bus"})
        text = V.build_vector_text(record)
        self.assertIn("objects: bus, car\n", text)


class IndexBuildTest(unittest.TestCase):
    def test_dimensions_and_count(self):
        records = [_record(f"v:f{i}", obj="car") for i in range(5)]
        tmp, manifest = _build(records)
        try:
            from qdrant_client import QdrantClient
            client = QdrantClient(path=str(Path(tmp.name) / "idx"))
            info = client.get_collection(V.COLLECTION)
            self.assertEqual(info.config.params.vectors.size, 384)
            self.assertEqual(str(info.config.params.vectors.distance), "Cosine")
            self.assertEqual(client.count(V.COLLECTION).count, 5)
            points, _ = client.scroll(V.COLLECTION, limit=10, with_vectors=True)
            self.assertEqual(len(points[0].vector), 384)
            client.close()
        finally:
            tmp.cleanup()
        self.assertEqual(manifest["records_indexed"], 5)
        self.assertEqual(manifest["records_failed"], 0)

    def test_payload_only_evidence_id(self):
        records = [_record("v:f0", obj="car")]
        tmp, _ = _build(records)
        try:
            from qdrant_client import QdrantClient
            client = QdrantClient(path=str(Path(tmp.name) / "idx"))
            points, _ = client.scroll(V.COLLECTION, limit=10)
            self.assertEqual(points[0].payload, {"evidence_id": "v:f0"})
            client.close()
        finally:
            tmp.cleanup()

    def test_deterministic_point_mapping(self):
        records = [_record(f"v:f{i}") for i in range(4)]
        tmp, _ = _build(records)
        try:
            from qdrant_client import QdrantClient
            client = QdrantClient(path=str(Path(tmp.name) / "idx"))
            points, _ = client.scroll(V.COLLECTION, limit=10)
            mapping = {p.id: p.payload["evidence_id"] for p in points}
            self.assertEqual(mapping, {i: f"v:f{i}" for i in range(4)})
            client.close()
        finally:
            tmp.cleanup()

    def test_resumable_second_run(self):
        records = [_record(f"v:f{i}") for i in range(3)]
        tmp = tempfile.TemporaryDirectory()
        try:
            out = Path(tmp.name) / "idx"
            first = V.build_index(records, out, model=FakeModel(), batch_size=2)
            second = V.build_index(records, out, model=FakeModel(), batch_size=2)
            self.assertEqual(first["records_indexed"], 3)
            self.assertEqual(second["records_indexed"], 3)
            self.assertEqual(second["records_failed"], 0)
        finally:
            tmp.cleanup()

    def test_manifest_contents(self):
        records = [_record("v:f0")]
        tmp, manifest = _build(records)
        try:
            for key in ("corpus_sha256", "records_total", "records_indexed",
                        "records_failed", "embedding_model", "model_revision",
                        "sentence_transformers_version", "qdrant_client_version",
                        "vector_dimension", "distance", "normalization",
                        "evidence_text_schema", "collection", "built_utc",
                        "elapsed_seconds"):
                self.assertIn(key, manifest, key)
            self.assertEqual(manifest["records_total"], 1)
            self.assertEqual(manifest["vector_dimension"], 384)
            self.assertEqual(manifest["distance"], "COSINE")
            self.assertEqual(manifest["collection"], V.COLLECTION)
            self.assertEqual(manifest["embedding_model"], V.MODEL_ID)
            saved = json.loads((Path(tmp.name) / "idx" / "manifest.json")
                               .read_text(encoding="utf-8"))
            self.assertEqual(saved["corpus_sha256"], manifest["corpus_sha256"])
        finally:
            tmp.cleanup()

    def test_empty_invalid_evidence(self):
        tmp, manifest = _build([{"no_id": True}, "junk"])
        try:
            self.assertEqual(manifest["records_indexed"], 0)
            self.assertEqual(manifest["records_failed"], 2)
        finally:
            tmp.cleanup()


class QdrantRetrieverTest(unittest.TestCase):
    def _store(self, directory, dim=8):
        import numpy as np

        from src.pipeline.vector_store import (
            QdrantVectorRetriever, open_collection)

        class FakeModel:
            def __init__(self):
                self.seen = []

            def encode(self, texts, batch_size=64, normalize_embeddings=True,
                       show_progress_bar=False, convert_to_numpy=True):
                self.seen.extend(texts)
                fixed = {"alpha": 0, "beta": 1, "gamma": 2}
                basis = np.zeros((len(texts), dim))
                for i, text in enumerate(texts):
                    basis[i, fixed.get(text, dim - 1)] = 1.0
                return basis

        model = FakeModel()
        client = open_collection(directory, "t", dimension=dim)
        from qdrant_client.models import PointStruct
        vectors = model.encode(["alpha", "beta", "gamma"])
        client.upsert("t", points=[
            PointStruct(id=0, vector=list(map(float, vectors[0])),
                        payload={"evidence_id": "v:f0"}),
            PointStruct(id=1, vector=list(map(float, vectors[1])),
                        payload={"evidence_id": "v:f1"}),
            PointStruct(id=2, vector=list(map(float, vectors[2])),
                        payload={"evidence_id": "v:f2"})])
        client.close()
        retriever = QdrantVectorRetriever(directory, "t", model_id="fake",
                                         model=model)
        return retriever, model

    def test_query_verbatim_and_method(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            retriever, model = self._store(tmp)
            try:
                model.seen.clear()
                out = retriever.search("alpha", top_k=2)
                self.assertEqual(model.seen, ["alpha"])
                self.assertEqual(out[0].evidence_id, "v:f0")
                self.assertEqual(out[0].rank, 1)
                self.assertTrue(all(r.retrieval_method == "vector" for r in out))
                self.assertEqual(len(out), 2)
            finally:
                retriever.close()

    def test_score_preservation_and_order(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            retriever, _ = self._store(tmp)
            try:
                out = retriever.search("alpha", top_k=3)
                scores = [r.score for r in out]
                self.assertEqual(scores, sorted(scores, reverse=True))
                self.assertAlmostEqual(scores[0], 1.0, places=5)
                self.assertEqual([r.rank for r in out], [1, 2, 3])
            finally:
                retriever.close()

    def test_top_k_cap(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            retriever, _ = self._store(tmp)
            try:
                self.assertEqual(len(retriever.search("alpha", top_k=1)), 1)
            finally:
                retriever.close()

    def test_model_constants(self):
        from src.pipeline import vector_store as V

        self.assertEqual(V.MODEL_ID,
                         "sentence-transformers/all-MiniLM-L6-v2")
        self.assertEqual(V.DIMENSION, 384)
        self.assertIsInstance(V.model_revision("definitely-not-a-model"), str)

    def test_scope_filtering_in_adapter(self):
        import tempfile

        from src.pipeline import retrieval_eval as E

        records = [
            {"evidence_id": "v:f0", "video_id": "v", "start_time": 0.0, "end_time": 2.0},
            {"evidence_id": "w:f0", "video_id": "w", "start_time": 0.0, "end_time": 2.0},
            {"evidence_id": "v:f1", "video_id": "v", "start_time": 50.0, "end_time": 52.0},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            retriever, _ = self._store(tmp)
            try:
                entry = {"query_id": "Q", "query": "alpha",
                         "scope": {"video_id": "v", "start_time": 0.0, "end_time": 10.0}}
                out = E.vector_search_for_judgment(records, entry, retriever, top_k=10)
                self.assertEqual([r.evidence_id for r in out], ["v:f0"])
                self.assertEqual(out[0].rank, 1)
                self.assertEqual(out[0].retrieval_method, "vector")
            finally:
                retriever.close()

    def test_empty_scope_yields_empty(self):
        import tempfile

        from src.pipeline import retrieval_eval as E

        records = [{"evidence_id": "v:f0", "video_id": "v", "start_time": 0.0,
                    "end_time": 2.0}]
        with tempfile.TemporaryDirectory() as tmp:
            retriever, _ = self._store(tmp)
            try:
                entry = {"query_id": "Q", "query": "alpha",
                         "scope": {"video_id": "missing", "start_time": None,
                                   "end_time": None}}
                self.assertEqual(
                    E.vector_search_for_judgment(records, entry, retriever), [])
            finally:
                retriever.close()


if __name__ == "__main__":
    unittest.main()
