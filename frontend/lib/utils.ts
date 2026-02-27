// Utility functions

/**
 * Compute confidence (0–1) from Sales vs Risk score variance.
 *
 * Mirrors backend `_confidence_from_variance(sales_score, risk_score)`.
 * Confidence reflects consensus strength — higher disagreement → lower confidence.
 *
 * Mapping:
 *   variance  0–10  → 90–100% confidence
 *   variance 10–20  → 70–90%
 *   variance 20–40  → 50–70%
 *   variance  >40   → <50% (floor at 10%)
 */
export function confidenceFromVariance(
    salesScore: number,
    riskScore: number,
): number {
    const variance = Math.abs(salesScore - riskScore);

    let confidence: number;
    if (variance <= 10) {
        confidence = 1.0 - 0.01 * variance;
    } else if (variance <= 20) {
        confidence = 0.9 - 0.02 * (variance - 10);
    } else if (variance <= 40) {
        confidence = 0.7 - 0.01 * (variance - 20);
    } else {
        confidence = Math.max(0.1, 0.5 - 0.005 * (variance - 40));
    }

    return Math.round(confidence * 100) / 100;
}
