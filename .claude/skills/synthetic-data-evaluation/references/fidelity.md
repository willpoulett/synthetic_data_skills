# Fidelity

## Our fidelity tiers vs V-Star

The V-Star framework defines fidelity levels for synthetic data evaluation. Our tiers overlap in
intent but differ in focus: V-Star emphasises statistical resemblance to a real comparator; ours
are designed for NHS healthcare datasets where real comparator data may not be available, and where
the distinction between "realistic generation" and "validated against real data" is the key
boundary.

### Team fidelity tiers

| Tier | Focus | What it means |
| --- | --- | --- |
| **Low** | Data structure and valid values | Correct columns, data types, valid codes, plausible marginals. Data looks like it should structurally. Independent sampling — no conditional relationships. |
| **Medium** | Inter-variable relationships look realistic | Everything in Low, plus: realistic join cardinalities (twins, multiple spells, censored pregnancies, NICE-schedule contacts), realistic missingness, univariate distributions calibrated to published NHS statistics, conditional sampling (age→parity, BMI→GDM, previous CS→delivery method), rare events at published prevalence with clinically coherent cascades, additional tables (e.g. MSD405, MSD109, MSD107 for MSDS), configurable fairness mode. |
| **High** | Mostly indistinguishable from real data | Same generation approach as Medium. The difference is validation: High fidelity is earned by evaluating against real comparator data (KS tests, JS divergence, discriminator AUC, TSTR, privacy audit) and confirming realistic distributions including rare values. A grade, not a generation mode. |

Low → Medium is a generation improvement. Medium → High is primarily a validation improvement.
Without real data to compare against, the best claim is Medium.

## Evaluation levels (L0–L3)

Four evaluation levels, increasing in difficulty and decreasing in tool support. Run in order; a
dataset failing an earlier level does not need a later one yet. Record each level separately in
report section 7 — a single combined score hides which level failed, and the levels have different
remedies.

## Level 0 — schema conformance

Prerequisite before any statistical check. Validates that the generated output matches the
specification structurally.

Checks:
- **Column presence**: every field the spec defines exists as a column, regardless of mandation
  level (M, R, D all produce columns)
- **Column count**: no extra or missing columns per table
- **Data types**: each column's values conform to the declared type
- **Mandatory non-null**: M fields have no missing values
- **Required population**: R fields are populated where the condition applies
- **Derived presence**: D fields exist as columns (value may be NULL where derivation notes say so)
- **Code list validation**: every coded field contains only values from its declared code list
  (codes are strings — "01" ≠ 1)
- **Cross-table foreign keys**: IDs referenced across tables exist in the parent table

When a machine-readable schema exists in `schemas/`, load it and automate these checks. Manual
inspection of column names against a 200-field spec is error-prone.

A dataset failing L0 should not proceed to L1 — fix the schema failures first.

## Level 1 — univariate

Individual column distributions: means, variances, category frequencies, missingness rates,
ranges. Table stakes. Necessary, not sufficient.

## Level 2 — multivariate

Correlations and joint distributions. Most tools are weak here, and it is where cross-modal
coherence becomes measurable.

Check correlation structure, conditional distributions (distribution of a lab value given a
diagnosis), and for multi-modal datasets, agreement across modalities for the same patient.

Cross-modal coherence has no dedicated metric in the audit. Apply multivariate fidelity across
files: derive comparable features per modality and test agreement. Examples:

| Pair | Test |
| --- | --- |
| ECG ↔ observations table | Heart rate derived from the waveform vs the recorded value |
| Clinical note ↔ labs table | Values stated in prose vs the structured record |
| Note ↔ pathway | Conditions and medications mentioned vs those on the record at that date |
| Wearable ↔ functional status | Derived activity and sleep biomarkers vs recorded status |
| Genotype ↔ phenotype | Variants assigned vs conditions in the patient state |
| Any modality ↔ timeline | Artefact timestamps vs encounter dates |

Independent per-modality generation appears here as correlations near zero where clinical knowledge
requires them. The remedy is the patient state in the generation skill, not a re-run of the metric.

## Level 3 — clinical fidelity

Domain logic a clinician would catch immediately. Statistical fidelity is not sufficient for
healthcare. Examples: no pregnant males; lab values consistent with the stated diagnosis;
plausible medication–condition pairings.

Extend per modality in play: genotype supporting phenotype, notes asserting only recorded facts,
signal features matching the patient's condition and medication.

This rarely has an off-the-shelf metric; it is a rules-based layer written in-house. Do not search
for a library.

## Tools

| Tool | Use for | Verdict | Constraints |
| --- | --- | --- | --- |
| SynthGauge | Metrics and visualisations comparing feature distributions between real and synthetic data. `Evaluator` class gives a consistent interface; multiple instances compare generators on the same metrics | Use | Covers levels 1–2. No clinical logic |
| synthcity | Fidelity metrics alongside utility and privacy in one suite, with healthcare plugins | Maybe | PyTorch — flag before use. Prefer when already used for generation |

Comparability is the reason to prefer SynthGauge: a single generator scoring 0.8 means little; two
generators scored on identical metrics is informative.

No other fidelity tool is sanctioned. Adding one requires user approval and a source URL.

## Script

`scripts/clinical_rules.py` — not built. Declarative clinical-plausibility checker: rules defined
as data (condition → expected lab range, condition → plausible medications, impossible field
combinations), applied row-wise, returning pass/fail with offending records.

Deterministic, re-run on every dataset, and unreliable when done by inspection — a model asked to
eyeball 5,000 rows will miss violations and invent others. Build it sized to the first real
dataset's rules.

## P-value thresholds (from MSDS proof-of-concept)

No universal thresholds have been agreed (SKILL.md Rule 4). These were used in the MSDS evaluation
and are a reasonable starting point:

| Check type | Threshold | Interpretation |
| --- | --- | --- |
| Most distribution checks (chi-squared, binomial) | p > 0.01 → PASS | Cannot reject that synthetic matches target |
| Delivery method / high-DOF categoricals | p > 0.001 → PASS | More degrees of freedom needs a more lenient threshold |
| Correlations | r > 0.1 and p < 0.05 → PASS | Standard direction — low p = significant correlation present |

**P-values read backwards for distribution checks.** High p = PASS (cannot reject match). This is
the opposite of typical research use. Reports must explain this.

## NHS TOS datasets

For datasets with a TOS, L0 schema checks must verify all mandation levels (M, R, D). See
`synthetic-data-generation/references/nhs-datasets.md` for the D-field categories and which
should contain values vs NULL.

## No real comparator

Levels 1 and 2 require a reference distribution. Without one:

- Level 3 becomes the primary evidence.
- Check internal consistency instead: observed prevalences, age structure and comorbidity patterns
  against the cohort definition in report section 3, and modalities against each other using the
  table above.
- Compare against published distributions where the user supplies them; record the source.
- State in report section 7 which levels did not run and why.

## Report

Section 7. Record the tool used, the result per level, and levels that could not run. Pair with the
privacy result from section 9 — high fidelity is also high leakage (`privacy.md`). When level 2
fails on cross-modal agreement, name the specific disagreement when handing back to
`synthetic-data-generation`.
