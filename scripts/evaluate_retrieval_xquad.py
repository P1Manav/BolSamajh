"""Evaluate multilingual vector retrieval hit@k on Google XQuAD Hindi dataset.

Adheres to Tier 2 Requirement 12:
- Uses Google XQuAD Hindi validation set (CC-BY-SA-4.0).
- Indexes context paragraphs into DocumentRetriever.
- Evaluates Top-1, Top-3, and Top-5 Hit Rate on Hindi queries.
- Measures cosine similarity score distributions for relevant vs irrelevant queries
  to empirically justify the refusal threshold.
- Outputs results to benchmark_data/retrieval_benchmark.json.
"""

import sys
import json
import time
from pathlib import Path

from huggingface_hub import hf_hub_download
import pyarrow.parquet as pq
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from bolsamajh.documents.loader import Document, DocumentPage
from bolsamajh.documents.retriever import DocumentRetriever

RESULTS_FILE = ROOT_DIR / "benchmark_data" / "retrieval_benchmark.json"


def evaluate_xquad_retrieval(num_samples: int = 50) -> dict:
    print(f"Downloading Google XQuAD Hindi validation split...")
    parquet_path = hf_hub_download(
        repo_id="google/xquad",
        filename="xquad.hi/validation-00000-of-00001.parquet",
        repo_type="dataset"
    )
    table = pq.read_table(parquet_path)
    print(f"Loaded {len(table)} XQuAD Hindi QA pairs.")

    # Unique context passages
    contexts = []
    seen_contexts = set()
    qa_pairs = []

    for i in range(len(table)):
        ctx = table["context"][i].as_py()
        q = table["question"][i].as_py()
        ans = table["answers"][i].as_py()["text"][0] if table["answers"][i].as_py()["text"] else ""

        if ctx not in seen_contexts:
            seen_contexts.add(ctx)
            contexts.append(ctx)

        qa_pairs.append({
            "question": q,
            "context": ctx,
            "answer": ans
        })

        if len(seen_contexts) >= num_samples:
            break

    print(f"Indexing {len(contexts)} unique Hindi context passages into DocumentRetriever...")
    
    # Create synthetic Document with pages
    doc = Document(
        title="XQuAD Hindi Evaluation Corpus",
        source="google/xquad/xquad.hi",
        pages=[DocumentPage(text=c, page_number=i+1, source="xquad.hi") for i, c in enumerate(contexts)]
    )

    retriever = DocumentRetriever(
        embedding_model="intfloat/multilingual-e5-base",
        chunk_size=380,
        chunk_overlap=40,
        refusal_threshold=0.0, # Disable threshold during hit@k measurement
    )
    
    t0 = time.time()
    num_chunks = retriever.index_document(doc)
    index_time = time.time() - t0
    print(f"Indexed {num_chunks} chunks in {index_time:.2f}s.")

    # Evaluate hit@k
    eval_qas = qa_pairs[:num_samples]
    hit_1 = 0
    hit_3 = 0
    hit_5 = 0
    relevant_scores = []
    latencies = []

    print(f"Evaluating {len(eval_qas)} Hindi retrieval queries...")
    for item in eval_qas:
        q = item["question"]
        target_ctx = item["context"]

        t_start = time.perf_counter()
        results = retriever.retrieve(q, top_k=5, apply_threshold=False)
        latencies.append((time.perf_counter() - t_start) * 1000.0)

        # Check if target context matches retrieved chunks
        match_ranks = []
        for rank, chunk in enumerate(results, 1):
            # Check overlap between chunk text and target context
            if target_ctx[:80] in chunk.text or chunk.text[:80] in target_ctx:
                match_ranks.append(rank)
                relevant_scores.append(chunk.score)

        if match_ranks:
            best_rank = min(match_ranks)
            if best_rank <= 1:
                hit_1 += 1
            if best_rank <= 3:
                hit_3 += 1
            if best_rank <= 5:
                hit_5 += 1

    # Measure irrelevant queries to establish refusal threshold baseline
    irrelevant_queries = [
        "What is the airspeed velocity of an unladen swallow?",
        "Quantum entanglement in superconductors",
        "Python GIL implementation details in CPython 3.12",
        "Mars rover perseverance launch trajectory",
        "Recipe for authentic Hyderabadi biryani"
    ]
    irrelevant_scores = []
    for iq in irrelevant_queries:
        res = retriever.retrieve(iq, top_k=3, apply_threshold=False)
        for r in res:
            irrelevant_scores.append(r.score)

    total_eval = len(eval_qas)
    summary = {
        "dataset": "google/xquad (xquad.hi)",
        "license": "CC-BY-SA-4.0",
        "num_passages": len(contexts),
        "num_queries": total_eval,
        "embedding_model": retriever.embedding_model_name,
        "hit_at_1_pct": round(hit_1 / total_eval * 100, 2),
        "hit_at_3_pct": round(hit_3 / total_eval * 100, 2),
        "hit_at_5_pct": round(hit_5 / total_eval * 100, 2),
        "mean_latency_ms": round(float(np.mean(latencies)), 2),
        "p95_latency_ms": round(float(np.percentile(latencies, 95)), 2),
        "relevant_score_mean": round(float(np.mean(relevant_scores)), 3) if relevant_scores else 0.0,
        "relevant_score_p10": round(float(np.percentile(relevant_scores, 10)), 3) if relevant_scores else 0.0,
        "irrelevant_score_max": round(float(np.max(irrelevant_scores)), 3) if irrelevant_scores else 0.0,
        "recommended_refusal_threshold": round(float(np.max(irrelevant_scores)) + 0.05, 2) if irrelevant_scores else 0.55,
    }

    print("\n=======================================================")
    print(" XQuAD Hindi Multilingual Retrieval Benchmark Results")
    print("=======================================================")
    print(f" Embedding Model:     {summary['embedding_model']}")
    print(f" Hit@1:               {summary['hit_at_1_pct']}%")
    print(f" Hit@3:               {summary['hit_at_3_pct']}%")
    print(f" Hit@5:               {summary['hit_at_5_pct']}%")
    print(f" Mean Latency:        {summary['mean_latency_ms']} ms")
    print(f" Relevant Mean Score: {summary['relevant_score_mean']}")
    print(f" Irrelevant Max Score:{summary['irrelevant_score_max']}")
    print(f" Recommended Refusal: {summary['recommended_refusal_threshold']}")
    print("=======================================================")

    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"[OK] Saved retrieval benchmark results to {RESULTS_FILE}")

    return summary


if __name__ == "__main__":
    evaluate_xquad_retrieval(num_samples=30)
