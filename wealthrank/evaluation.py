"""Deterministic, SYNTHETIC evaluation—not real user A/B evidence.

Proxy relevance and click propensities are declared explicitly. Metrics only
demonstrate an offline experiment harness, not expected investment returns.
"""
import numpy as np


def _dcg(rel: np.ndarray) -> float:
    if len(rel) == 0:
        return 0.0
    return float(np.sum((2 ** rel - 1) / np.log2(np.arange(2, len(rel) + 2))))


def ndcg_at_k(relevance: np.ndarray, ranks: np.ndarray, k: int = 5) -> float:
    picks = relevance[ranks[:k]]
    ideal = np.sort(relevance)[::-1][:k]
    denominator = _dcg(ideal)
    return _dcg(picks) / denominator if denominator else 0.0


def precision_at_k(relevance: np.ndarray, ranks: np.ndarray, k: int = 5) -> float:
    return float(np.mean(relevance[ranks[:k]] >= 2))


def run_synthetic_lab(seed: int = 42, profiles: int = 100, k: int = 5) -> dict:
    rng = np.random.default_rng(seed)
    methods = ("Sector only", "Hybrid", "No risk feature", "No sector feature")
    ndcg = {m: [] for m in methods}
    precision = {m: [] for m in methods}
    clicks = {m: 0 for m in ("Sector only", "Hybrid")}
    impressions = profiles * k
    for _ in range(profiles):
        preferred_sector = int(rng.integers(0, 6))
        target_risk = float(rng.uniform(.10, .60))
        sectors = rng.integers(0, 6, size=24)
        volatility = rng.uniform(.08, .85, size=24)
        liquid = rng.random(24) > .10
        sector_match = (sectors == preferred_sector).astype(float)
        risk_match = np.maximum(0, 1 - abs(volatility - target_risk) / .60)
        # Artificial labels are constructed independently of the ranking's weights.
        utility = .45 * sector_match + .45 * risk_match + .10 * liquid
        relevance = np.digitize(utility, [.42, .68])  # 0, 1, 2
        noise = rng.normal(0, .08, 24)
        scored = {
            "Sector only": sector_match + noise,
            "Hybrid": .47 * sector_match + .48 * risk_match + .05 * liquid + noise,
            "No risk feature": .85 * sector_match + .15 * liquid + noise,
            "No sector feature": .90 * risk_match + .10 * liquid + noise,
        }
        for method, score in scored.items():
            ranks = np.argsort(-score, kind="stable")
            ndcg[method].append(ndcg_at_k(relevance, ranks, k))
            precision[method].append(precision_at_k(relevance, ranks, k))
            if method in clicks:
                for j in ranks[:k]:
                    probability = .06 + .18 * (relevance[j] / 2)
                    clicks[method] += int(rng.random() < probability)
    baseline = clicks["Sector only"] / impressions
    treatment = clicks["Hybrid"] / impressions
    return {
        "profiles": profiles, "candidates_per_profile": 24, "top_k": k,
        "ndcg": {m: float(np.mean(ndcg[m])) for m in methods},
        "precision": {m: float(np.mean(precision[m])) for m in methods},
        "ctr": {"Sector only": baseline, "Hybrid": treatment},
        "relative_lift": (treatment / baseline - 1) if baseline else None,
        "seed": seed,
    }
