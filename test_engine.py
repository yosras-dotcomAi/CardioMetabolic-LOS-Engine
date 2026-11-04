import math
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from clinical_bmi_engine import (CARDIAC_HISTORY_EXTRA_DAYS, TIERS, calculate_bmi,
                                 classify_bmi, estimate_extra_bed_days,
                                 evaluate_clinical_risk)


@pytest.mark.parametrize("bmi, expected", [
    (18.49, "Underweight"), (18.5, "Normal weight"), (24.99, "Normal weight"),
    (25.0, "Overweight"), (29.95, "Overweight"), (30.0, "Obesity Class I"),
    (34.95, "Obesity Class I"), (35.0, "Obesity Class II"),
    (39.95, "Obesity Class II"), (40.0, "Obesity Class III"), (55.0, "Obesity Class III"),
])
def test_boundaries_have_no_gaps(bmi, expected):
    # Values such as 24.95 or 29.95 used to fall between tiers and be misclassified.
    assert classify_bmi(bmi).name == expected


def test_tiers_are_contiguous():
    for a, b in zip(TIERS, TIERS[1:]):
        assert a.upper == b.lower
    assert TIERS[0].lower == 0 and math.isinf(TIERS[-1].upper)


def test_calculate_bmi():
    assert calculate_bmi(70, 175) == 22.86


@pytest.mark.parametrize("w, h", [(0, 170), (70, 0), (-5, 170), (5, 170), (70, 20), (70, 400)])
def test_invalid_inputs_raise(w, h):
    with pytest.raises(ValueError):
        calculate_bmi(w, h)


def test_cardiac_history_adds_days_only_when_bmi_30_or_more():
    base = evaluate_clinical_risk(32.0, False)["LOS uplift (days, planning assumption)"]
    with_cardiac = evaluate_clinical_risk(32.0, True)["LOS uplift (days, planning assumption)"]
    assert round(with_cardiac - base, 1) == CARDIAC_HISTORY_EXTRA_DAYS
    low = evaluate_clinical_risk(27.0, False)["LOS uplift (days, planning assumption)"]
    assert evaluate_clinical_risk(27.0, True)["LOS uplift (days, planning assumption)"] == low


def test_scenario_total():
    summary = estimate_extra_bed_days([(22.0, False), (31.0, False), (36.0, True)])
    assert summary["patients"] == 3
    assert summary["extra_bed_days"] == round(0 + 1.5 + 2.3 + 1.0, 1)
