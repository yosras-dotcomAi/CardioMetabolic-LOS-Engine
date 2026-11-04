# Cardiometabolic Risk & Hospital Stay Stratifier (CRSS)

> **Please read first:** This is a **portfolio and learning project**, not a validated clinical tool and not medical advice. The length-of-stay (LOS) values are **illustrative planning assumptions**, not published effect sizes. The relationship between BMI and outcomes after cardiac procedures is complex and varies between studies, so replace these numbers with your own hospital's LOS data before using the logic for any real planning.

## What it does
A small rule-based Python tool for inpatient and cath lab capacity discussions:
1. Calculates BMI from weight and height.
2. Classifies BMI using the [WHO adult categories](https://www.who.int/news-room/fact-sheets/detail/obesity-and-overweight).
3. Attaches a **planning assumption** (extra bed days, priority, suggested pathway) to each category.
4. Runs "what if" scenarios: given a cohort of patients, how many extra bed days would these assumptions add?

## Why I built it
In the cath lab I see how patient factors affect planning: access-site choice, recovery, and bed demand. This project turns that conversation into code that a nurse manager or bed coordinator can adjust and test.

## BMI tiers and planning assumptions
| BMI (kg/m²) | WHO category | Priority | Assumed extra LOS | Suggested pathway |
|---|---|---|---|---|
| below 18.5 | Underweight | Moderate | +1.2 days | Clinical nutrition assessment and frailty screening |
| 18.5 to 24.9 | Normal weight | Routine | Baseline | Standard clinical care and discharge protocol |
| 25.0 to 29.9 | Overweight | Low-Moderate | +0.5 days | Preventive lifestyle counselling and outpatient follow-up |
| 30.0 to 34.9 | Obesity Class I | High | +1.5 days | Pre-cath-lab vascular assessment and early ambulation protocol |
| 35.0 to 39.9 | Obesity Class II | Critical | +2.3 days | Enhanced recovery pathway and VTE prophylaxis review |
| 40.0 and above | Obesity Class III | Urgent | +3.8 days | Multidisciplinary care team (cardiology, bariatric, ICU liaison) |

Patients with a BMI of 30 or more **and** cardiac history get an extra **+1.0 day** (also an assumption). All values live in one table at the top of `clinical_bmi_engine.py` (`TIERS`), so they are easy to change.

## Example output
```text
Patient: 105 kg, 172 cm, cardiac history
BMI: 35.49 (Obesity Class II, Critical priority)
LOS uplift: +3.3 days (includes +1.0 day for cardiac history)

Scenario: 8 example patients
extra_bed_days: 14.3  |  extra_bed_days_per_patient: 1.79
```

## How to run
```bash
git clone https://github.com/yosras-dotcomAi/CardioMetabolic-LOS-Engine.git
cd CardioMetabolic-LOS-Engine
python clinical_bmi_engine.py
```
Run the tests (21 tests, including every tier boundary):
```bash
pip install pytest
pytest
```

## Quality notes
- **Tier boundaries have no gaps.** Each tier includes its lower limit and excludes its upper limit, so values such as 24.95 or 29.95 are classified correctly. The tests check this.
- **Inputs are validated:** impossible weights and heights raise a clear error.
- **No real hospital or patient data** is used anywhere. The demo values are invented.

## Limitations
- LOS uplifts are assumptions, not evidence.
- BMI alone does not capture body composition, frailty, or procedure complexity.
- It is a planning calculator, not a prediction model: it has not been fitted to or tested on real outcomes.

## Possible next step
Fit the tier values to real (approved, anonymised) LOS data, then compare the rule-based estimate with the actual bed days.

## Author
**Yosra El Nagar**, Cath Lab Head Nurse moving into Healthcare Data Analytics
[LinkedIn](https://www.linkedin.com/in/yosra-nagar-9a6862118/) | [GitHub](https://github.com/yosras-dotcomAi)
