"""Evaluate multilingual vector retrieval and calibrate refusal threshold on Google XQuAD Hindi.

Calibrates refusal threshold on at least 200 relevant queries and 200 irrelevant/unanswerable queries
by maximizing F1 score between answered-relevant and refused-irrelevant.
Outputs results to benchmark_data/retrieval_benchmark.json.
"""

import json
import sys
import time
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
from huggingface_hub import hf_hub_download

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from bolsamajh.documents.loader import Document, DocumentPage
from bolsamajh.documents.retriever import DocumentRetriever

RESULTS_FILE = ROOT_DIR / "benchmark_data" / "retrieval_benchmark.json"

OFF_TOPIC_QUERIES = [
    "What is the airspeed velocity of an unladen swallow?",
    "Quantum entanglement in high-temperature superconductors",
    "Python GIL implementation details in CPython 3.12",
    "Mars rover perseverance launch trajectory and atmospheric entry",
    "Recipe for authentic Hyderabadi dum biryani with saffron",
    "How to configure WireGuard VPN on Ubuntu 24.04 LTS",
    "Rules of cricket LBW decision review system",
    "Photosynthesis light-dependent reactions in chloroplasts",
    "History of the Roman Empire and the fall of Constantinople",
    "Stock market options pricing using Black-Scholes formula",
    "Black hole event horizon and Hawking radiation mechanism",
    "Differential equations solution methods using Laplace transforms",
    "Baking sourdough bread with hydration percentages",
    "DNA replication enzymes and Okazaki fragments",
    "Kubernetes ingress controller configuration and TLS termination",
    "Neurotransmitters dopamine and serotonin synaptic transmission",
    "Plate tectonics and continental drift theory",
    "Rust borrow checker memory safety semantics",
    "How to play chess Sicilian Defense Najdorf variation",
    "SpaceX Starship orbital refuelling architecture",
]


def evaluate_and_calibrate(num_relevant: int = 200, num_irrelevant: int = 200) -> dict:
    print("Downloading Google XQuAD Hindi validation split...")
    parquet_path = hf_hub_download(
        repo_id="google/xquad",
        filename="xquad.hi/validation-00000-of-00001.parquet",
        repo_type="dataset",
    )
    table = pq.read_table(parquet_path)
    total_rows = len(table)
    print(f"Loaded {total_rows} XQuAD Hindi QA pairs.")

    # 1. Partition into indexed passages and un-indexed passages
    indexed_contexts = []
    seen_contexts = set()
    indexed_qa = []
    unindexed_qa = []

    # Target: index first 60 unique contexts (~200 questions map to these)
    max_indexed_contexts = 60

    for i in range(total_rows):
        ctx = table["context"][i].as_py()
        q = table["question"][i].as_py()
        ans = table["answers"][i].as_py()["text"][0] if table["answers"][i].as_py()["text"] else ""

        if ctx not in seen_contexts:
            if len(indexed_contexts) < max_indexed_contexts:
                seen_contexts.add(ctx)
                indexed_contexts.append(ctx)
                indexed_qa.append({"question": q, "context": ctx, "answer": ans})
            else:
                unindexed_qa.append({"question": q, "context": ctx, "answer": ans})
        else:
            if ctx in indexed_contexts:
                indexed_qa.append({"question": q, "context": ctx, "answer": ans})
            else:
                unindexed_qa.append({"question": q, "context": ctx, "answer": ans})

    # Prepare relevant queries
    relevant_set = indexed_qa[:num_relevant]
    print(f"Indexed corpus has {len(indexed_contexts)} passages.")
    print(f"Selected {len(relevant_set)} relevant queries matching indexed passages.")

    # Prepare irrelevant queries (un-indexed passage queries + off-topic queries)
    irrelevant_queries = [
        item["question"] for item in unindexed_qa[: num_irrelevant - len(OFF_TOPIC_QUERIES)]
    ]
    irrelevant_queries.extend(OFF_TOPIC_QUERIES)
    irrelevant_queries = irrelevant_queries[:num_irrelevant]
    print(
        f"Prepared {len(irrelevant_queries)} unanswerable/irrelevant queries (not in indexed corpus)."
    )

    # Index document corpus into DocumentRetriever
    doc = Document(
        title="XQuAD Hindi Evaluation Corpus",
        source="google/xquad/xquad.hi",
        pages=[
            DocumentPage(text=c, page_number=idx + 1, source="xquad.hi")
            for idx, c in enumerate(indexed_contexts)
        ],
    )

    retriever = DocumentRetriever(
        embedding_model="intfloat/multilingual-e5-base",
        chunk_size=380,
        chunk_overlap=40,
        refusal_threshold=0.0,
    )

    t0 = time.time()
    num_chunks = retriever.index_document(doc)
    print(f"Indexed {num_chunks} chunks in {time.time() - t0:.2f}s.")

    # Evaluate relevant queries
    print("Evaluating relevant queries...")
    hit_1 = 0
    hit_3 = 0
    hit_5 = 0
    latencies = []
    relevant_eval_records = []

    for item in relevant_set:
        q = item["question"]
        target_ctx = item["context"]

        t_start = time.perf_counter()
        results = retriever.retrieve(q, top_k=5, apply_threshold=False)
        latencies.append((time.perf_counter() - t_start) * 1000.0)

        top_score = results[0].score if results else 0.0
        match_rank = None
        for rank, chunk in enumerate(results, 1):
            if target_ctx[:70] in chunk.text or chunk.text[:70] in target_ctx:
                match_rank = rank
                break

        if match_rank is not None:
            if match_rank <= 1:
                hit_1 += 1
            if match_rank <= 3:
                hit_3 += 1
            if match_rank <= 5:
                hit_5 += 1

        relevant_eval_records.append(
            {
                "top_score": top_score,
                "is_correct_passage": match_rank is not None and match_rank <= 5,
            }
        )

    # Evaluate irrelevant queries
    print("Evaluating irrelevant queries...")
    irrelevant_eval_scores = []
    for iq in irrelevant_queries:
        t_start = time.perf_counter()
        results = retriever.retrieve(iq, top_k=3, apply_threshold=False)
        latencies.append((time.perf_counter() - t_start) * 1000.0)
        top_score = results[0].score if results else 0.0
        irrelevant_eval_scores.append(top_score)

    # Calibrate Refusal Threshold via F1 Optimization
    threshold_candidates = np.arange(0.65, 0.88, 0.005)
    best_f1 = -1.0
    best_threshold = 0.76
    best_metrics = {}

    for t in threshold_candidates:
        # Relevant: TP if top_score >= t and correct; FN otherwise
        tp = sum(
            1 for r in relevant_eval_records if r["top_score"] >= t and r["is_correct_passage"]
        )
        fn = len(relevant_eval_records) - tp

        # Irrelevant: FP if top_score >= t (falsely answered); TN if top_score < t (correctly refused)
        fp = sum(1 for s in irrelevant_eval_scores if s >= t)
        tn = sum(1 for s in irrelevant_eval_scores if s < t)

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

        if f1 > best_f1:
            best_f1 = f1
            best_threshold = round(float(t), 3)
            best_metrics = {
                "threshold": best_threshold,
                "precision": round(prec * 100, 2),
                "recall": round(rec * 100, 2),
                "f1_score": round(f1, 4),
                "true_positives": tp,
                "false_positives": fp,
                "true_negatives": tn,
                "false_negatives": fn,
            }

    summary = {
        "dataset": "google/xquad (xquad.hi)",
        "license": "CC-BY-SA-4.0",
        "num_passages": len(indexed_contexts),
        "num_relevant_queries": len(relevant_set),
        "num_irrelevant_queries": len(irrelevant_queries),
        "embedding_model": retriever.embedding_model_name,
        "hit_at_1_pct": round(hit_1 / len(relevant_set) * 100, 2),
        "hit_at_3_pct": round(hit_3 / len(relevant_set) * 100, 2),
        "hit_at_5_pct": round(hit_5 / len(relevant_set) * 100, 2),
        "mean_latency_ms": round(float(np.mean(latencies)), 2),
        "p95_latency_ms": round(float(np.percentile(latencies, 95)), 2),
        "calibrated_refusal_threshold": best_metrics["threshold"],
        "precision_pct": best_metrics["precision"],
        "recall_pct": best_metrics["recall"],
        "f1_score": best_metrics["f1_score"],
        "relevant_score_mean": round(
            float(np.mean([r["top_score"] for r in relevant_eval_records])), 3
        ),
        "irrelevant_score_mean": round(float(np.mean(irrelevant_eval_scores)), 3),
        "irrelevant_score_max": round(float(np.max(irrelevant_eval_scores)), 3),
    }

    print("\n=======================================================")
    print(" XQuAD Hindi Multilingual Retrieval Benchmark Results")
    print("=======================================================")
    print(f" Embedding Model:     {summary['embedding_model']}")
    print(
        f" Corpus Passages:     {summary['num_passages']} (Corpus size limitation: 60 unique passages)"
    )
    print(f" Relevant Queries:    {summary['num_relevant_queries']}")
    print(f" Irrelevant Queries:  {summary['num_irrelevant_queries']}")
    print(f" Hit@1:               {summary['hit_at_1_pct']}%")
    print(f" Hit@3:               {summary['hit_at_3_pct']}%")
    print(f" Hit@5:               {summary['hit_at_5_pct']}%")
    print(f" Mean Latency:        {summary['mean_latency_ms']} ms")
    print(f" Calibrated Threshold:{summary['calibrated_refusal_threshold']}")
    print(f" Precision:           {summary['precision_pct']}%")
    print(f" Recall:              {summary['recall_pct']}%")
    print(f" F1 Score:            {summary['f1_score']}")
    print("=======================================================")

    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"[OK] Saved retrieval benchmark results to {RESULTS_FILE}")

    # Save to calibrated_thresholds.json for runtime config/retriever consumption
    cal_thresholds_file = ROOT_DIR / "benchmark_data" / "calibrated_thresholds.json"
    current_thresholds = {
        "intfloat/multilingual-e5-base": 0.785,
        "intfloat/multilingual-e5-small": 0.760,
    }
    if cal_thresholds_file.exists():
        try:
            with open(cal_thresholds_file, "r", encoding="utf-8") as f:
                current_thresholds.update(json.load(f))
        except Exception:
            pass
    current_thresholds[summary["embedding_model"]] = summary["calibrated_refusal_threshold"]
    with open(cal_thresholds_file, "w", encoding="utf-8") as f:
        json.dump(current_thresholds, f, indent=2, ensure_ascii=False)
    print(f"[OK] Saved calibrated thresholds to {cal_thresholds_file}")

    # Run English & Gujarati Sanity Checks
    run_english_gujarati_sanity_check(retriever)

    return summary


def run_english_gujarati_sanity_check(retriever: DocumentRetriever):
    """Sanity checks on English and Gujarati corpora.

    Note: Google XQuAD does not offer a Gujarati split; we evaluate on a curated
    Gujarati sanity corpus with FLEURS-style sentences.
    """
    print("\n--- Running English & Gujarati Retrieval Sanity Checks ---")

    # 1. English Sanity Check
    en_passages = [
        "The Apollo 11 mission was the first spaceflight that landed humans on the Moon.",
        "Python is a high-level, general-purpose programming language known for readability.",
        "The Pacific Ocean is the largest and deepest of Earth's oceanic divisions.",
        "Photosynthesis is a biological process used by plants to synthesize nutrients from light.",
        "The Reserve Bank of India is the central bank of India responsible for the currency.",
    ]
    en_queries = [
        ("Which mission landed the first humans on the Moon?", 0),
        ("What programming language is known for its high readability?", 1),
        ("What is the largest ocean on Earth?", 2),
    ]
    en_doc = Document(
        title="English Sanity Corpus",
        source="sanity://en",
        pages=[
            DocumentPage(text=p, page_number=i + 1, source="sanity://en")
            for i, p in enumerate(en_passages)
        ],
    )
    retriever.index_document(en_doc)
    en_hits = 0
    for q, exp_idx in en_queries:
        res = retriever.retrieve(q, top_k=1, apply_threshold=False)
        if res and en_passages[exp_idx][:30] in res[0].text:
            en_hits += 1
    print(f"[+] English Sanity Hits: {en_hits}/{len(en_queries)}")

    # 2. Gujarati Sanity Check
    print("Note: Google XQuAD has no Gujarati split. Evaluating curated Gujarati sanity corpus.")
    gu_passages = [
        "ગાંધીનગર ગુજરાત રાજ્યનું પાટનગર છે જે સાબરમતી નદીના કિનારે આવેલું છે.",
        "ગુજરાતનું ક્ષેત્રફળ લગભગ ૧,૯૬,૦૨૪ ચોરસ કિલોમીટર છે અને લાંબો દરિયાકિનારો છે.",
        "ગીર રાષ્ટ્રીય ઉદ્યાન એશિયાઈ સિંહોનું એકમાત્ર કુદરતી રહેઠાણ છે.",
        "ગુજરાતી સાહિત્યમાં નરસિંહ મહેતાને આદિકવિ માનવામાં આવે છે.",
        "અમદાવાદ ભારતનું સૌપ્રથમ વર્લ્ડ હેરિટેજ સિટી તરીકે જાહેર કરવામાં આવ્યું હતું.",
    ]
    gu_queries = [
        ("ગુજરાત રાજ્યનું પાટનગર કયું છે?", 0),
        ("એશિયાઈ સિંહો કયા રાષ્ટ્રીય ઉદ્યાનમાં જોવા મળે છે?", 2),
        ("ભારતનું પ્રથમ વર્લ્ડ હેરિટેજ સિટી કયું છે?", 4),
    ]
    gu_doc = Document(
        title="Gujarati Sanity Corpus",
        source="sanity://gu",
        pages=[
            DocumentPage(text=p, page_number=i + 1, source="sanity://gu")
            for i, p in enumerate(gu_passages)
        ],
    )
    retriever.index_document(gu_doc)
    gu_hits = 0
    for q, exp_idx in gu_queries:
        res = retriever.retrieve(q, top_k=1, apply_threshold=False)
        if res and gu_passages[exp_idx][:20] in res[0].text:
            gu_hits += 1
    print(f"[+] Gujarati Sanity Hits: {gu_hits}/{len(gu_queries)}")


if __name__ == "__main__":
    evaluate_and_calibrate(num_relevant=200, num_irrelevant=200)
