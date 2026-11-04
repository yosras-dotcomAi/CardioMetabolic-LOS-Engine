"""Cardiometabolic Risk & Hospital Stay Stratifier (CRSS).

A rule-based planning tool for inpatient and cath lab capacity discussions.

What it does
  1. Calculates BMI from weight and height.
  2. Classifies BMI using the WHO categories.
  3. Attaches a length-of-stay (LOS) planning ASSUMPTION and a suggested
     pathway to each category, so a unit can test "what if" bed-day scenarios.

What it is NOT
  The LOS values below are illustrative planning assumptions, not published
  effect sizes, and this is not a validated clinical decision tool. Replace the
  numbers in TIERS with your own hospital's LOS data before any real use.
"""

import math
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Tuple


@dataclass(frozen=True)
class BMITier:
    """One BMI category. `upper` is exclusive, so there are no gaps between tiers."""
    name: str
    lower: float
    upper: float
    los_uplift_days: float
    priority: str
    pathway: str
    reason: str


# WHO adult BMI categories. LOS uplifts are ASSUMPTIONS (see module docstring).
TIERS: Tuple[BMITier, ...] = (
    BMITier("Underweight", 0.0, 18.5, 1.2, "Moderate",
            "Clinical nutrition assessment and frailty screening",
            "Frailty and malnutrition risk"),
    BMITier("Normal weight", 18.5, 25.0, 0.0, "Routine",
            "Standard clinical care and discharge protocol",
            "Baseline"),
    BMITier("Overweight", 25.0, 30.0, 0.5, "Low-Moderate",
            "Preventive lifestyle counselling and outpatient follow-up",
            "Mild metabolic risk"),
    BMITier("Obesity Class I", 30.0, 35.0, 1.5, "High",
            "Pre-cath-lab vascular assessment and early ambulation protocol",
            "Increased procedural and vascular access risk"),
    BMITier("Obesity Class II", 35.0, 40.0, 2.3, "Critical",
            "Enhanced recovery pathway and VTE prophylaxis review",
            "Higher wound, thromboembolic and ICU bed risk"),
    BMITier("Obesity Class III", 40.0, math.inf, 3.8, "Urgent",
            "Multidisciplinary care team (cardiology, bariatric, ICU liaison)",
            "Severe cardiopulmonary and readmission vulnerability"),
)

# Extra bed days added for patients with obesity (BMI of 30 or more) AND cardiac history.
CARDIAC_HISTORY_EXTRA_DAYS = 1.0


def calculate_bmi(weight_kg: float, height_cm: float) -> float:
    """Calculate Body Mass Index (kg/m2), rounded to 2 decimals."""
    if not (10 <= weight_kg <= 500):
        raise ValueError("Weight must be between 10 and 500 kg.")
    if not (50 <= height_cm <= 250):
        raise ValueError("Height must be between 50 and 250 cm.")
    height_m = height_cm / 100.0
    return round(weight_kg / (height_m ** 2), 2)


def classify_bmi(bmi: float) -> BMITier:
    """Return the WHO tier for a BMI value."""
    if not (bmi > 0) or math.isnan(bmi):
        raise ValueError("BMI must be a positive number.")
    for tier in TIERS:
        if tier.lower <= bmi < tier.upper:
            return tier
    raise ValueError(f"No tier found for BMI {bmi}.")  # unreachable for valid input


def evaluate_clinical_risk(bmi: float, has_cardiac_history: bool = False) -> Dict[str, Any]:
    """Stratify a patient and return the planning assumptions for their tier."""
    tier = classify_bmi(bmi)
    uplift = tier.los_uplift_days
    pathway = tier.pathway
    if has_cardiac_history and bmi >= 30.0:
        uplift += CARDIAC_HISTORY_EXTRA_DAYS
        pathway += " plus targeted heart failure and vascular monitoring"

    if uplift == 0:
        los_text = "Baseline (standard care pathway)"
    else:
        los_text = f"+{uplift:.1f} days ({tier.reason})"
        if uplift > tier.los_uplift_days:
            los_text += f" including +{CARDIAC_HISTORY_EXTRA_DAYS:.1f} day for cardiac history"

    return {
        "BMI": bmi,
        "WHO Category": tier.name,
        "Strategic Resource Priority": tier.priority,
        "LOS uplift (days, planning assumption)": round(uplift, 1),
        "Estimated Inpatient LOS Impact": los_text,
        "Recommended Clinical Transformation Pathway": pathway,
    }


def estimate_extra_bed_days(patients: Iterable[Tuple[float, bool]]) -> Dict[str, Any]:
    """Scenario helper: total extra bed days for a cohort of (bmi, has_cardiac_history)."""
    counts: Dict[str, int] = {}
    total = 0.0
    n = 0
    for bmi, cardiac in patients:
        result = evaluate_clinical_risk(bmi, cardiac)
        counts[result["WHO Category"]] = counts.get(result["WHO Category"], 0) + 1
        total += result["LOS uplift (days, planning assumption)"]
        n += 1
    return {
        "patients": n,
        "patients_per_category": counts,
        "extra_bed_days": round(total, 1),
        "extra_bed_days_per_patient": round(total / n, 2) if n else 0.0,
    }


if __name__ == "__main__":
    print("=== Cardiometabolic Risk & Hospital Stay Stratifier: demo (illustrative data) ===")
    bmi = calculate_bmi(weight_kg=105.0, height_cm=172.0)
    result = evaluate_clinical_risk(bmi, has_cardiac_history=True)
    for key, value in result.items():
        print(f"{key}: {value}")

    print("\n--- Scenario: 8 example patients (bmi, cardiac history) ---")
    cohort = [(22.4, False), (27.1, False), (31.0, True), (33.8, False),
              (36.5, True), (41.2, True), (17.9, False), (29.95, False)]
    summary = estimate_extra_bed_days(cohort)
    for key, value in summary.items():
        print(f"{key}: {value}")
