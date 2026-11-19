---
name: synthetic-data-evaluation
description: Assesses synthetic healthcare data along fidelity, utility and privacy. Use when asked whether synthetic data is good, realistic, clinically plausible, useful or safe to share; for univariate and multivariate distribution comparison, clinical-plausibility rule checks, TSTR (train-on-synthetic / test-on-real), synthetic-vs-real discriminator tests, membership- and attribute-inference or re-identification risk, disclosure control, free-text leakage, a privacy audit before a dataset leaves the environment, or an evaluation report for a generated dataset. Also use immediately after generating any dataset with the synthetic-data-generation skill, including the "no real seed data" case where TSTR is impossible. Covers SynthGauge, synthcity metrics, TAPAS/SAS and PrivFingerprint.
---

# Synthetic healthcare data evaluation

Every generated dataset gets an evaluation, recorded in its `REPORT.md`. This skill decides which
checks can run and routes to the method detail.

The tools tables in `references/` are the recommended inventory. You must ask for user approval if
using an unlisted tool. Where no tool exists for a check, the reference file says so.

## Rules

**1. Read the report before interpreting any result.** Section 4 gives the seeding case, which
fixes what can run at all. Section 5 gives label provenance: if one LLM produced both the content
and its label, a strong utility score may only show that a model can read what another model wrote.
A result read without those two is not evidence.

**2. Fidelity and privacy are one reading, not two.** Data reproducing real records exactly is both
maximally faithful and maximally leaky. The discriminator check has a floor and a ceiling: easily
separable means poor fidelity, not separable at all is a privacy alarm. Never report a fidelity
result without the privacy result beside it.

**3. Do not ingest real patient data to run a check.** The output of a check over real data is
itself a disclosure question. Where a check structurally requires real data — membership inference,
exact-match — stop and confirm with the user how and by whom it should be run. It may be a
human-run step.

**4. No pass/fail thresholds.** None has been agreed, and inventing one would be false precision.
Report what was measured, what was not, and why, so the reader can judge fitness for their own use.

**5. An unrun check is "not established", never "safe".** This applies to the free-text leakage
assessment and the safe-to-share verdict especially. Say what would need to run to establish it.

**6. Schema checks use the full specification.** When a technical specification exists, every field
it defines for a generated table must be present in the output — regardless of mandation level. A
derived field missing from the output is a schema failure, not something outside the evaluator's
scope. Load the same machine-readable schema the generator used (from `schemas/`) and validate all
field classifications, not just "mandatory" and "required."

## Axes

**Fidelity** — does it look like real data. Four levels: schema conformance (L0), univariate
(column distributions), multivariate (correlations and joint structure), clinical (domain logic a
clinician would catch). → `references/fidelity.md`

**Utility** — is it useful for the task. TSTR: train on synthetic, test on held-out real, compare
against a real-trained baseline. Lighter checks: ML comparison, synthetic-vs-real discriminator.
→ `references/utility.md`

**Privacy** — does it leak. Exact-match checks are necessary and not sufficient; membership and
attribute inference are the real test. → `references/privacy.md`

Writing or completing the dataset report → `references/report.md`

## Local scripts

`scripts/call_llm.py` — `call_llm(prompt, model=..., temp=0.7, ...) -> str | None`, plus
`call_llm_async` for batches. It returns `None` when every attempt fails; check before using the
result. Two rules specific to evaluation:

- **Try to pass a different `model` than the one that generated the text.** A model asked to find
  identifying detail in its own output under-reports it — the label-validity trap in privacy form.
  Where the environment exposes only one model, use it, and record in report section 9 that
  generation and extraction shared a model and that the result is therefore a lower bound on
  what is identifying. This is what makes LLM entity extraction a viable substitute for GLiNER and
  spaCy (`references/privacy.md`).
- **LLM extraction is not reproducible.** No seed is exposed and `temp` defaults to 0.7. Acceptable
  for exploration and flagging, too weak for a score that must be defended. Record which of the two
  it is.

`scripts/clinical_rules.py` — **not built.** Declarative clinical-plausibility rule checker.
Interface in `references/fidelity.md`.

`scripts/tstr.py` — **not built.** TSTR harness plus discriminator AUC, sklearn only. Interface in
`references/utility.md`.

Build either when a real dataset needs it, not speculatively. Both are deterministic checks that
are unreliable done by inspection — a model asked to eyeball 5,000 rows will miss violations and
invent others.

## Checklist

Copy this into your response and tick items off as you go. Doing a step implicitly does not tick
its box.

```
Evaluation progress:
- [ ] 1. REPORT.md sections 1-6 read; seeding case and label provenance established before any result is interpreted
- [ ] 1a. Machine-readable schema loaded (if one exists); all field classifications identified
- [ ] 2. Scope fixed — which checks can run, which need real data, which need user permission
- [ ] 3. Tools acquired and verified — installed in .venv and smoke-tested, or recorded as not runnable
- [ ] 4a. Fidelity L0: schema conformance against full specification (all mandation levels, column counts, code lists)
- [ ] 4b. Fidelity L1-L3: univariate, multivariate, clinical — run or explicitly recorded as not run and why
- [ ] 5. Utility: TSTR against a real holdout, or the substitution named as a substitution
- [ ] 6. Privacy: checks run; nothing requiring real data run without user confirmation
- [ ] 7. Fidelity and privacy read against each other before either is reported
- [ ] 8. REPORT.md sections 7-10 written; verdict is safe to share / not safe to share / not established
```

## Step 1 — read the report

Sections 1-6 of the dataset's `REPORT.md`, before running anything. Two fix the scope of everything
that follows:

- **Section 4, seeding case** — real seed data, schema only, or from intelligence. Step 2 turns this
  into the list of checks that can run.
- **Section 5, label provenance** — whether labels were derived from the patient state before the
  content existing. If they were not, utility results are discounted rather than presented
  (Rule 1).

If sections 1-6 are missing or thin, the dataset was not generated through the
**synthetic-data-generation** skill's Step 7. Say so and reconstruct what you can before evaluating;
record in section 10 what could not be reconstructed.

If a machine-readable schema exists in `schemas/`, load it now. It is the authority for field names,
mandation levels, code lists, and derivation rules used in L0 checks.

## Step 2 — establish what can run

Determine the claimed fidelity level and whether real data exists for comparison.

### Fidelity tiers

The fidelity tier claimed by the generator determines which checks are expected:

| Tier | Required checks |
| --- | --- |
| Low | L0 schema conformance, L1 univariate vs published stats, L2 cross-table FKs |
| Medium | All low checks plus statistical tests (binomial, chi-squared, Pearson) against published distributions |
| High | All medium checks plus validation against real data (KS, JS divergence, discriminator, TSTR, privacy audit) |

High fidelity is earned by evidence, not by generation method. Without real data to compare
against, the best claim is medium.

### Scope by data availability

| Situation | Fidelity | Utility | Privacy |
| --- | --- | --- | --- |
| Real seed data used, available for comparison | Full | TSTR against real holdout | Mandatory; direct leakage risk |
| Real data exists, not used for generation | Full, as reference distribution | TSTR if the holdout is representative | Required; lower risk |
| No real data | Clinical + internal consistency only | TSTR impossible — see **No real seed data** | Lower risk; re-check if any real record informed a prompt |

### Specification-aware checks

When a machine-readable schema exists, add these checks regardless of seeding case:

- L0 schema conformance against the full specification (all mandation levels)
- Column count verification per table
- Code list validation for every coded field
- Cross-table foreign key integrity

These checks are free — they need no real data and catch the most common generation bugs.

Anything in the scope table that needs real data is subject to Rule 3: confirm with the user
before it runs, and confirm who runs it.

## Step 3 — acquire and verify tools

Nothing in `references/` has been verified by running it; the tables record repository claims.
Install from PyPI into `.venv` and smoke-test on a small slice before reporting any number from it.

TAPAS is the one worth the attempt first. It is recorded as inspiration with no setup notes, but
the repository shows a pip-installable package with a CLI, and if it installs it is the only real
adversarial audit available (`references/privacy.md`). Most of the strongest privacy tools are
inspiration-only, so the runnable set is thinner than the tables imply.

Where a tool will not install or is inspiration-only, record it as not runnable and carry that into
report section 9. A check that could not run is not a check that passed (Rule 5).

## Step 4 — fidelity

Four levels, run in order; a dataset failing an earlier level does not need a later one yet. Record
each level separately — a combined score hides which level failed, and the levels have different
remedies. → `references/fidelity.md`

**L0 — schema conformance.** Every column the spec defines exists; every coded value is valid;
column counts match. This is prerequisite. See `references/fidelity.md` Level 0.

**L1 — univariate.** Column distributions vs published stats or the cohort definition.

**L2 — multivariate.** Correlations, joint distributions, cross-table consistency.

**L3 — clinical.** Domain logic a clinician would catch. Rules-based, written in-house. No
off-the-shelf metric; do not search for a library.

### Interpreting p-values

For distribution checks, p-values test the null hypothesis that the synthetic distribution matches
the target. This is the OPPOSITE of typical research:

- **High p-value = PASS** (cannot reject that synthetic matches target)
- **Low p-value = FAIL** (synthetic significantly differs from target)

Reports must include a "Reading the p-values" section explaining this.

Exception: correlation checks test whether correlations are PRESENT, so they use standard
interpretation (low p = significant correlation = PASS).

## Step 5 — utility

TSTR where a real holdout exists: train on synthetic, test on real, and report the real-trained
baseline and the gap beside it. A synthetic score alone is uninterpretable.
→ `references/utility.md`

Check label provenance from Step 1 before reading any result here. Where TSTR cannot run, see
**No real seed data** below — do not drop the axis or let fidelity stand in for it.

## Step 6 — privacy

Weakest to strongest: exact-match, attribute inference, membership inference, adversarial auditing.
Exact-match is necessary and nowhere near sufficient. → `references/privacy.md`

Rule 3 governs this step. Membership inference and exact-match structurally require real data
alongside the synthetic; stop and confirm rather than running them unprompted. Free text is the
leakage path structured metrics miss.

## Step 7 — read fidelity against privacy

Before writing either result. A high fidelity score and a clean privacy result are consistent; a
high fidelity score and an undistinguishable discriminator are the same finding read twice, and the
reading is leakage (Rule 2).

**Discriminator AUC bands:**

| AUC | Reading |
| --- | --- |
| < 0.55 | Privacy alarm — too similar, possible memorisation |
| 0.55–0.75 | Good fidelity |
| 0.75–0.85 | Moderate fidelity |
| > 0.85 | Poor fidelity — easily distinguishable |

## Step 8 — write the report and the verdict

Complete sections 7-10 of the dataset's `REPORT.md`: fidelity, utility, privacy and disclosure,
limitations. Template and rules: `references/report.md`.

Reports must stand alone per fidelity level. Do not reference or compare to other fidelity levels
within a report.

The verdict is one of **safe to share**, **not safe to share**, **not established**. Where the
checks that would justify sharing could not run — inspiration-only tooling, or a check needing real
data that must not be touched — the answer is "not established", and the decision routes to the
user with a statement of what would settle it.

If results are poor, hand back to the **synthetic-data-generation** skill with the specific failure
— a broken correlation, an implausible medication pairing, a cross-modal mismatch — not a request
to regenerate. Then re-run the checks that failed.

### Human evaluation

Generated data will still need checking by a human to identify issues the automated checks miss.
If the reviewer is not familiar with dataset idiosyncrasies, find someone who is. Recommend
clinician review of a sample — with no real comparator it is the strongest validation available.

## No real seed data

TSTR cannot run. Do not drop the utility axis and report fidelity alone. Substitute, and label the
substitution in the report:

- Clinical plausibility becomes the primary quality signal (`references/fidelity.md`).
- Internal consistency replaces external fidelity: check the data against the patient state and
  cohort definition it was generated from, and check modalities against each other.
- Train and test on synthetic (TSTS) to establish that the encoded signal is learnable. A
  substantially weaker claim than TSTR; report it as such.
- Compare against published distributions where the user supplies them; record the source.
- State that downstream utility is unproven, in those words.
- Recommend clinician review of a sample. With no real comparator it is the strongest validation
  available.

### From-intelligence privacy

When the generator used no real data at any stage — no seed records, no real records in prompts, no
fitting to individual-level data — and the dataset contains no LLM-generated free text that could
surface memorised training content, the privacy stance is **"low risk by construction"**, not "not
established."

The generator has no mechanism to reproduce or approximate a real person's record. Post-hoc
comparison against real data (membership inference, exact-match) would introduce the very data
dependency the from-intelligence approach avoids. Do not list unrunnable checks as gaps — they
structurally do not apply.

This stance requires verifying:
- No real patient data was used at any generation stage
- No real records were pasted into LLM prompts
- Identifiers use synthetic ranges that cannot collide with real ones (e.g. NHS 999 test range)
- Free-text fields, if any, were generated from structured state, not from prompts containing real
  records

If any of these checks fail, the dataset is no longer purely from-intelligence and the standard
privacy evaluation applies.

Re-check whether LLM-generated free text surfaces memorised training content; and whether
invented records collide with real people by chance in a small, distinctive population.
