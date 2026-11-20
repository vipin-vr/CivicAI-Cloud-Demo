"""Priority calculations used by complaint submission."""
from __future__ import annotations

SEVERITY_SCORES = {"Low": 25, "Medium": 50, "High": 75, "Critical": 100}


def priority_label(score: float) -> str:
    if score < 30:
        return "Low"
    if score < 50:
        return "Medium"
    if score < 75:
        return "High"
    return "Critical"


def calculate_priority(severity: str, public_risk: int, public_impact: int) -> tuple[float, str, str]:
    severity_score = SEVERITY_SCORES.get(severity, 50)
    risk = max(0, min(100, int(public_risk)))
    impact = max(0, min(100, int(public_impact)))
    score = round(severity_score * 0.4 + risk * 0.3 + impact * 0.3, 1)
    label = priority_label(score)
    explanation = f"{label} priority ({score}/100): severity contributes {severity_score * .4:.1f}, public risk {risk * .3:.1f}, and public impact {impact * .3:.1f}."
    return score, label, explanation
