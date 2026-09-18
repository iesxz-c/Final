"""Phase 5A.2 - Local vector index over frozen Phase 2D fused evidence.

Builds a Qdrant collection (local file mode, no server) holding one
384-dim cosine vector per fused record, embedded with
sentence-transformers/all-MiniLM-L6-v2. No retrieval here; the
VectorRetriever implementation arrives in Phase 5A.3.

Deterministic evidence text (approved 5A.1), fixed section order,
sorted-unique labels, verbatim case. EXCLUDED on purpose: evidence_id,
video_id, source_references (filename-bearing: queries also contain
filenames, so including them would hand the vector leg a free
filename-matching signal), timestamps, anomaly_score, confidence.

Normalization is explicit: encode(..., normalize_embeddings=True), so
stored vectors are unit length and Qdrant COSINE is exact cosine
similarity. Point id = record position in evidence.json order, payload =
{evidence_id} only.

Usage:
    python -m src.pipeline.vector_store --help
    python -m src.pipeline.vector_store --evidence data/data_155n/fused_155/evidence.json --output-dir data/vector_155
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
COLLECTION = "fused_155"
DIMENSION = 384
TEXT_SCHEMA_VERSION = "vector-text/v1"


def build_vector_text(record: dict) -> str:
    """Deterministic embedding text for one fused record.

    Sections in fixed order; labels sorted-unique within each section;
    verbatim case. Only content labels: no ids, filenames, timestamps,
    scores, or confidences.
    """
    objects = sorted({str(d.get("class_name", "")).strip() for d in
                      record.get("object_evidence", []) or []
                      if str(d.get("class_name", "")).strip()})
    actions = sorted({str(e.get("label", "")).strip()
                      for e in record.get("generic_action_evidence", []) or []
                      for e in [e] + list(e.get("top_k", []) or [])
                      if str(e.get("label", "")).strip()})
    events = sorted({str(e.get("label", "")).strip()
                     for e in record.get("surveillance_event_evidence", []) or []
                     for e in [e] + list(e.get("top_k", []) or [])
                     if str(e.get("label", "")).strip()})
    return (f"objects: {', '.join(objects)}\n"
            f"actions: {', '.join(actions)}\n"
            f"events: {', '.join(events)}")


def corpus_sha256(records: list) -> str:
    """Hash over evidence_id order (stable corpus fingerprint)."""
    digest = hashlib.sha256()
    for record in records:
        digest.update(str(record.get("evidence_id", "")).encode("utf-8")
                      if isinstance(record, dict) else repr(record).encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


def model_revision(model_id: str = MODEL_ID) -> str:
    """Resolved Hugging Face commit hash, or 'unresolved' offline."""
    try:
        from huggingface_hub import HfApi
        return HfApi().model_info(model_id).sha or "unresolved"
    except Exception:  # noqa: BLE001 - recorded honestly, never fatal
        return "unresolved"


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "missing"


def load_model(model_id: str = MODEL_ID):
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(model_id)


def embed_texts(model, texts: list, batch_size: int = 64) -> list:
    """Unit-length vectors (normalization explicit at encode time)."""
    vectors = model.encode(texts, batch_size=batch_size, normalize_embeddings=True,
                           show_progress_bar=False, convert_to_numpy=True)
    return [list(map(float, row)) for row in vectors]


def open_collection(path: str | Path, collection: str = COLLECTION,
                    dimension: int = DIMENSION):
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams

    client = QdrantClient(path=str(path))
    if not client.collection_exists(collection):
        client.create_collection(collection,
                                 vectors_config=VectorParams(size=dimension,
                                                             distance=Distance.COSINE))
    return client


class QdrantVectorRetriever:
    """Deterministic vector backend over the frozen local collection.

    Embeds the ORIGINAL query verbatim with the frozen model/revision/
    normalization, searches Qdrant (cosine), and returns RetrievalResults
    with preserved similarity scores. No keyword extraction, no rewrites,
    no synonyms, no rule-derived terms.
    """

    METHOD = "vector"

    def __init__(self, store_path: str | Path, collection: str = COLLECTION,
                 model_id: str = MODEL_ID, model=None):
        from qdrant_client import QdrantClient

        self.store_path = str(store_path)
        self.collection = collection
        self.model_id = model_id
        self.model = model if model is not None else load_model(model_id)
        self.model_revision = model_revision(model_id)
        self.client = QdrantClient(path=self.store_path)

    def close(self) -> None:
        self.client.close()

    def search(self, query: str, top_k: int = 10) -> list:
        """Embed query verbatim; return global top-k (scope applied by caller)."""
        from src.pipeline.retrieval_eval import RetrievalResult

        vectors = embed_texts(self.model, [str(query)])
        results = self.client.query_points(self.collection, query=vectors[0],
                                           limit=max(1, top_k)).points
        return [RetrievalResult(evidence_id=p.payload.get("evidence_id"),
                                rank=pos, score=float(p.score),
                                retrieval_method=self.METHOD)
                for pos, p in enumerate(results, 1)]


def existing_point_ids(client, collection: str) -> set:
    """Point ids already stored (for resumable builds)."""
    ids: set = set()
    offset = None
    while True:
        points, offset = client.scroll(collection, limit=4096, offset=offset,
                                       with_payload=False, with_vectors=False)
        ids.update(p.id for p in points)
        if offset is None:
            return ids


def build_index(records: list, output_dir: str | Path,
                collection: str = COLLECTION, model_id: str = MODEL_ID,
                batch_size: int = 64, model=None) -> dict:
    """Embed every record and upsert into Qdrant (resumable, deterministic).

    Point id = record position in input order. Records already present are
    skipped, so an interrupted build resumes by re-running the same
    command. Returns the manifest dict (also written to disk).
    """
    from qdrant_client.models import PointStruct

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    if model is None:
        model = load_model(model_id)
    started = datetime.now(timezone.utc).isoformat()
    t0 = time.perf_counter()
    client = open_collection(output_dir, collection)
    done = existing_point_ids(client, collection)
    failures: list = []
    ok = 0
    order: list = []

    def _flush() -> None:
        nonlocal ok
        texts = [build_vector_text(records[i]) for i in order]
        try:
            vectors = embed_texts(model, texts, batch_size=batch_size)
        except Exception as exc:  # noqa: BLE001 - recorded per record
            for i in order:
                failures.append({"evidence_id": records[i].get("evidence_id"),
                                 "error": str(exc)[:200]})
            return
        points = [PointStruct(id=i, vector=vec,
                              payload={"evidence_id": records[i].get("evidence_id")})
                  for i, vec in zip(order, vectors)]
        client.upsert(collection, points=points)
        ok += len(points)

    for i, record in enumerate(records):
        if not isinstance(record, dict) or not record.get("evidence_id"):
            failures.append({"evidence_id": record.get("evidence_id")
                             if isinstance(record, dict) else None,
                             "error": "missing evidence_id"})
            continue
        if i in done:
            ok += 1
            continue
        order.append(i)
        if len(order) >= batch_size:
            _flush()
            order.clear()
    if order:
        _flush()
    elapsed = round(time.perf_counter() - t0, 1)
    manifest = {
        "corpus_sha256": corpus_sha256(records),
        "records_total": len(records),
        "records_indexed": ok,
        "records_failed": len(failures),
        "failures": failures,
        "embedding_model": model_id,
        "model_revision": model_revision(model_id),
        "sentence_transformers_version": package_version("sentence-transformers"),
        "qdrant_client_version": package_version("qdrant-client"),
        "vector_dimension": DIMENSION,
        "distance": "COSINE",
        "normalization": "normalize_embeddings=True at encode (unit vectors)",
        "evidence_text_schema": TEXT_SCHEMA_VERSION,
        "collection": collection,
        "output_dir": str(output_dir),
        "built_utc": started,
        "elapsed_seconds": elapsed,
    }
    with (output_dir / "manifest.json").open("w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)
    return manifest


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 5A.2: build local vector index")
    parser.add_argument("--evidence", default=None)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--collection", default=COLLECTION)
    parser.add_argument("--model", default=MODEL_ID)
    parser.add_argument("--batch-size", type=int, default=64)
    args = parser.parse_args(argv)

    evidence = Path(args.evidence) if args.evidence else \
        PROJECT_ROOT / "data/data_155n/fused_155/evidence.json"
    output_dir = Path(args.output_dir) if args.output_dir else \
        PROJECT_ROOT / "data/vector_155"
    try:
        with evidence.open("r", encoding="utf-8") as fh:
            records = json.load(fh)
        if not isinstance(records, list) or not records:
            raise ValueError("evidence must be a non-empty JSON list")
    except (OSError, ValueError) as exc:
        print(f"vector store error: bad evidence: {exc}")
        return 2
    try:
        manifest = build_index(records, output_dir, args.collection, args.model,
                               args.batch_size)
    except Exception as exc:  # noqa: BLE001 - CLI reports plainly
        print(f"vector store error: build failed: {exc}")
        return 2
    print(f"indexed {manifest['records_indexed']}/{manifest['records_total']} "
          f"({manifest['records_failed']} failed) in {manifest['elapsed_seconds']}s "
          f"-> {output_dir} [{manifest['collection']}]")
    print(f"model {manifest['embedding_model']} rev {manifest['model_revision']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
