---
name: synthetic-data-generation
description: Generates synthetic healthcare data for AI proof-of-concepts: tabular and EHR records, patient pathways, clinical notes and free text, physiological signals and wearables (ECG, PPG, EEG), speech and dialogue audio, genomics (VCF, genotypes, expression) and medical imaging. Use when asked to generate, synthesise, simulate, mock or fabricate patient data, test data, a synthetic cohort or a demo dataset; when choosing between tools such as Faker, Synthea, SynPath, synthcity, NeuroKit2 or SDialog; and when building from real seed data, from a schema only, or from no seed data at all — including multi-modal cohorts that must stay coherent per patient.
---

# Synthetic healthcare data generation

Read only the reference files the request needs.

The tools tables in `references/` are the recommended inventory. You must ask for user approval if using an unlisted tool.

## Rules

**1. Coherence over per-modality fidelity.** No tool in `references/` coordinates with another.
Generate every modality from one shared patient state, taking the lower per-modality fidelity
where higher would break the shared story.

**2. Labels separate from data.** Derive labels from the patient state before generating the
content that expresses them. Never let one LLM call produce both a narrative and its ground-truth
annotation. Validate against real holdout data where it exists.

**3. Privacy.** Synthetic is not automatically private, especially when fitted to real data.
Nothing leaves the environment without a privacy audit. Do not put real patient data into a tool,
a prompt or a privacy checker.

**4. Environment gate.** Prefer pure-Python, pip-installable tools. Flag Java, Julia, R, GPU,
PyTorch, large model downloads and pinned environments before they become the plan.

**5. Inspiration assets are patterns, not installs.** Where an asset uses a specialist library for
a step, an LLM call or plain Python usually substitutes — that is the point. Each reference file
carries a per-asset entry: pattern, what to copy, what to substitute, what not to inherit,
caveats. For detail an entry lacks, clone under Step 3 or ask the user. Never make a network fetch
part of a generated dataset's method; the target environment may have no outbound access.

**6. Specification-first.** When a technical specification exists for the target dataset (a TOS,
data dictionary, HL7/FHIR profile, schema document), it is the single source of truth for what
the output must contain. Read the entire specification before generating. Extract it into a
machine-readable schema that captures every metadata column, not just field names and types. If the
specification has separate columns for "description" and "derivation/computation rules", the rules
column is the authority for what value to produce — descriptions say what a field IS, derivation
rules say what value it currently HAS. When the two disagree, the rules column wins.

## Local scripts

`scripts/call_llm.py` — the project's LLM entry point, against Foundry-hosted models.

```python
call_llm(prompt, model="...gpt-5-1", temp=0.7, max_attempts=5, chat_history=None) -> str | None
call_llm_async(...)   # same call, semaphore-limited; use for per-patient batches
```

`chat_history` is a flat alternating list `[user, assistant, user, ...]`; the prompt is appended as
the final user message.

- Use it wherever a step needs language rather than a library: narrative text, dialogue, free-text
  fields, and the substitutions in Rule 5.
- **Do not** use it to sample the patient state or derive labels. Those are code with a seeded RNG
  (Rules 1 and 2).
- **It returns `None` when every attempt fails.** Check before writing the result into a record —
  unchecked, `None` lands in the dataset as a string.
- **Output is not reproducible.** No seed is exposed and `temp` defaults to 0.7, so for
  LLM-generated fields report section 4 records model ID and temperature; a seed there would be a
  false claim. Pass `temp=0` when variation is not wanted — it narrows output but does not make it
  reproducible.
- Needs `FOUNDRY_HOSTNAME` and `TOKEN` in `.env`. Smoke-test a single call before any batch:
  retries back off quadratically, so one dead call burns ~9 minutes before returning `None`.

`scripts/extract_tos_schema.py` — parses any NHS TOS Excel into JSON. Use when generating any
TOS-defined dataset (MSDS, MHSDS, HES, ECDS, CSDS, IAPT). Captures field names, types, mandation
levels, national codes, and derivation notes.

## Checklist

Copy this into your response and tick items off as you go. Doing a step implicitly does not tick
its box.

```
Generation progress:
- [ ] 1. Scope agreed with user — dataset, fidelity tier, tables, record count, seeding case, output location, environment/licence risks raised
- [ ] 1a. Technical specification parsed into machine-readable schema (if spec exists); field classifications categorised; ambiguities raised with user
- [ ] 2. Pip-installable options assessed; chosen tool installed in .venv and smoke-tested, or an LLM call judged sufficient
- [ ] 3. Repos cloned to data_repos/ only where pip did not cover it; licence checked, commit SHA recorded
- [ ] 4. Data specification written (or verified against technical spec); every number has a recorded source
- [ ] 5. Patient state sampled in code with a seeded RNG; labels derived from it before any content exists
- [ ] 6. Every modality generated from that state — one clock, per-patient seeds; column counts verified against spec
- [ ] 7. REPORT.md sections 1-6 written
- [ ] 8. Handed to synthetic-data-evaluation
```

## Step 1 — agree scope and route

Settle modality, seeding case, dataset size and output location before reading anything else. Check
the request against **Not supported** below and raise any gap now, not after generating. Raise
environment and licence risk from the Constraints column here too — a PyTorch or Java dependency
discovered at Step 2 has already shaped the plan.

### Fidelity tiers

Agree the target fidelity tier with the user before generating:

| Tier | Generation | Evaluation | Typical volume |
| --- | --- | --- | --- |
| Low | Schema-correct: valid field names, valid codes, plausible marginals, independent sampling | Schema checks, univariate distributions vs published stats, cross-table FKs | ~200 records |
| Medium | Conditional sampling with clinical dependency chains, rare event cascades, realistic missingness | All low checks plus statistical tests against published distributions | ~5,000 records |
| High | **A grade, not a generation mode.** Same generator as medium. | All medium checks plus validation against real comparator data (KS, JS divergence, discriminator, TSTR, privacy audit) | ~10,000+ records |

High fidelity is earned by evidence, not by generation method. Without real data to compare
against, high fidelity cannot be claimed. Each fidelity tier gets its own output folder (e.g.
`data/{dataset}_lowfi/`, `data/{dataset}_medfi/`).

### Questions to ask before generating

Pre-empt these in the brief to save iterations.

**About the dataset:**
- Which dataset? (exact name, version — "MSDS" is maternity, not mental health)
- Do you have the Technical Output Specification or equivalent schema?
- Which tables do you need?
- What fidelity level? (Low / Medium / High as defined above)
- How many records? (affects whether rare events appear at all)

**About the source material:**
- Are there published aggregate statistics? Where? (actual percentages, not prose)
- Will there be access to real source data? (determines IG requirements and max fidelity)
- Are there relevant clinical guidelines?
- Do you have code mapping tables? (code to category — often the single highest-value input)
- At what granularity are the published statistics? (overall aggregate vs per sub-population)

**About the use case:**
- What will this data be used for? (pipeline testing, demos, model training — shapes trade-offs)
- Does anyone need to sign off? (the evaluation report provides the evidence base)
- What environment will the generator run in?

### Seeding cases and IG implications

| Seeding case | What it means | IG needed? | Max fidelity claim |
| --- | --- | --- | --- |
| Basic table metadata | Column names, data types, example values | No | Low |
| From intelligence | Generated from published stats, schema specs, guidelines. No real patient data. | No | Medium |
| Schema only | Real data used to extract schema/metadata/summary stats, then discarded | Yes, for the extraction step | Medium |
| Real seed data | Generator fitted to real patient records | Yes, full. Privacy audit mandatory. | High |

### Route by modality

| Request | Read | First candidate |
| --- | --- | --- |
| Single table, flat records, schema to fill, multi-table | `references/tabular.md` | Faker/Mimesis; DataSynthesizer where distributions matter |
| Pathways, journeys, encounters over time, FHIR, activity data | `references/healthcare-ehr.md` | SynPath, Synthea/SyntheaUK as patterns |
| Notes, letters, discharge summaries, free text | `references/clinical-text.md` | SCN |
| ECG, PPG, respiration, EDA, EMG, EEG, wearables | `references/signals-wearables.md` | NeuroKit2 |
| Speech, consultation audio, dialogue, transcripts | `references/audio-speech.md` | SDialog |
| Genotypes, VCF, variants, expression, omics | `references/genomics.md` | HaploDynamics; msprime/stdpopsim for population realism |
| No seed data — build from domain knowledge | `references/from-intelligence.md` | Read before choosing any tool above |
| NHS TOS-defined dataset | `references/nhs-datasets.md` | Read alongside the modality file |

Multi-modal requests read several files. Dataset-specific reference files
(`references/msds.md`, `references/pathways.md`) carry conditional sampling chains,
known pitfalls, and external references for datasets that have been generated before.

### Route by seeding case

| Available | Approach |
| --- | --- |
| Real seed data, permitted | Fit a generator to it. Confirm permission first; privacy audit is then mandatory |
| Schema or metadata only | Template- and prior-driven generation (`references/tabular.md`); encode correlations explicitly |
| Domain knowledge only | Read `references/from-intelligence.md` first — this is a recorded open gap |

## Not supported

**Medical imaging** (CT, MRI, pathology, histology, DICOM, video). No reference file exists — too
little assessed material to route on. What is known: medigan offers pre-trained GANs (mammography,
brain MRI, chest X-ray, endoscopy, cardiac MRI) but is GPU-gated, with large models of unknown
feasibility in the target environment; MONAI is noted only in passing; RoentMod modifies existing
chest X-rays rather than generating new ones; video is computationally prohibitive; image privacy
auditing is unaddressed. State the position and confirm the approach before promising imaging.

Narrower gaps sit in their own files: handwritten and scanned letters (`clinical-text.md`); PSG
montages, Doppler/ultrasound, phone/mHealth passive sensing (`signals-wearables.md`); pathological
speech (`audio-speech.md`); proteomics, metabolomics, epigenomics, microbiome (`genomics.md`).

## Step 1a — parse and understand the specification

When the dataset has a technical specification (TOS, data dictionary, FHIR profile):

1. **Ask the user for the specification** if not already provided. Do not generate from field
   names alone when a spec exists.
2. **Extract a machine-readable schema** from the specification. Include every metadata column —
   mandation levels, data types, valid code lists, derivation rules, format constraints, linked
   tables. For NHS TOS datasets, use `scripts/extract_tos_schema.py`. Store the schema in
   `schemas/` for the evaluator.
3. **Identify all field classifications.** Every classified field must appear as a column in the
   output. The classification determines the field's VALUE, not whether the column EXISTS.
4. **Categorise derived/computed fields** before generating. Common categories: boilerplate,
   computable from other fields, clinically meaningful but placeholder, geographic lookups, code
   crosswalks, commissioning/pathway placeholders. Fields marked "placeholder" or "not yet
   implemented" must exist as columns but contain NULL.
5. **Ask the user for interpretation guidance** on anything ambiguous: how to read mandation
   levels, whether "derived" means "compute it" or "leave it NULL", which metadata columns are
   normative vs informational, whether code lists are open or closed.

Skip this step if no specification exists — proceed to Step 2.

## Step 2 — assess and install pip-installable tools

Start here, before any clone. Take the Step 1 candidates and judge fitness before installing:

- Does it produce the modality and the fields actually asked for?
- Does it clear the environment gate (Rule 4), or drag in PyTorch, Java, R or a large download?
- Would `call_llm()` do the same job with nothing to install? Where language is the output —
  narrative, dialogue, free-text fields — it usually will.

Install the choice into `.venv` and smoke-test it: run the tool's own minimal example and confirm
it produces output here. Nothing in `references/` has been verified by running it; the tables
record repository claims. If the smoke test fails, say so and return to Step 1 rather than
building a workaround.

## Step 3 — clone repos, only where needed

Only where Step 2 did not cover the need: the tool is not packaged, or the method matters more than
the package — every asset marked *inspiration*. Clone into `data_repos/` and read the source
locally.

Cloning is a development-time act in this environment, producing vendored code that runs offline in
the target environment. It does not make a fetch part of any dataset's method.

1. **Clone only what the tables list.** Approval and a recorded source URL come before the clone,
   not after.
2. **`data_repos/` is read-only reference.** Adapted code lands in `scripts/`. Do not edit a clone;
   the clone is provenance. `data_repos/` is gitignored.
3. **Check the licence before adapting, not after.** Reading does not bind you; copying does.
   MIT/Apache/BSD are adaptable with attribution. GPL/AGPL is infectious into whatever ships — stop
   and confirm before copying a line.
4. **Record repo URL, commit SHA, licence and date cloned** for report section 4. The SHA is the
   only honest answer to its Version column for a cloned tool.

## Step 4 — write the data specification

**If a technical specification exists (Step 1a):** The data specification is a subset of it —
which tables you are generating, which fields per table (all of them), and the clinical
distribution targets. Record which specification version you are working from. The spec determines
column names, types, code lists, and derivation rules; the data specification adds cohort size,
marginal distributions, and generation parameters.

**If no specification exists:** Write the specification from domain knowledge. For patient
populations this is a cohort definition and populates report section 3: size, age/sex structure,
condition prevalences, severity mix, comorbidity patterns, timeline span. For a single case or a
schema fill it is smaller — the fields, their ranges, and the clinical picture they must agree
with — but it is still written down.

Record the source of every number: real data, published statistic (cite), clinician estimate, or
"assumed". "Assumed" is a valid answer; an unrecorded number is not.

Adapt the specification to what the Step 2 tool can actually deliver, and note where the tool
narrowed it. That is why this step follows tool verification rather than preceding it.

With no real comparator, this specification is what the dataset is later evaluated against. Detail:
`references/from-intelligence.md`.

## Step 5 — define the patient state

Do this before generating anything, including for single-modality requests.

Write a per-patient state object: demographics, conditions with onset dates, medications, severity,
progression, encounter timeline. Sample it from the Step 4 specification in code with a seeded RNG
— not with an LLM, which collapses variety and produces distributions that cannot be audited.

- **Trajectory, not snapshot.** Decide the arc in the state; let modalities sample from it.
- **One clock.** All modalities share a single timeline.
- **Deterministic seeding.** One seed per patient per modality, derived from the patient ID.
- **Labels first.** Derive labels from the state before any content expressing them exists.
- **Ordered conditional sampling.** Dependencies must be sampled in declared order (e.g.
  age -> parity -> BMI -> delivery -> outcome). Independent sampling produces incoherent records.
  Declare the dependency chain before coding it.
- **Rare events need explicit cascades.** A stillbirth must propagate to Apgar=0, no
  breastfeeding, matching outcome codes. The AI will not infer all downstream effects unless told.
- **Watch for set membership shadowing in conditional logic.** if/elif chains where a general
  category matches before a specific one, so correctly-coded specific-case fixes never fire.
  Check specific-before-general ordering in every conditional adjustment.
- **Decompose published aggregates before using them as parameters.** A published end-to-end
  metric that maps to only one phase of a multi-phase process needs decomposing first:
  phase_value = published_total - other_phase_averages.
- **Each fix shifts the marginal distribution.** Re-check overall fit against published marginals
  after every batch of fixes, not just the issue you targeted.
- **NHS numbers must use the 999 test range.** Structurally impossible to collide with real numbers.

Precedent: the Coherent Data Set layers pathway data into a longitudinal record and attaches ECG,
imaging, notes and genomic data via FHIR resources when a patient has a relevant event. A research
artifact, not installable — replicate the approach. See `references/healthcare-ehr.md`.

## Step 6 — generate each modality from the state

Pass the state into every generator. Use parameterised simulators where they exist and `call_llm()`
only where language is required.

A modality generated from a fresh prompt rather than from the state loses coherence immediately,
surfacing in evaluation as correlations near zero where clinical knowledge requires them. The
remedy then is regeneration from the state, not a re-run of the metric.

After generating each table, verify that the column count matches the specification exactly. A
mismatch means fields are missing or extra columns have been introduced.

## Step 7 — write the report

Write `REPORT.md` alongside the data. Fill sections 1-6 (summary, intended use, cohort definition,
provenance, labels, coherence) at generation time, not retrospectively. Template and rules:
`.claude/skills/synthetic-data-evaluation/references/report.md`.

## Step 8 — evaluate

Hand the dataset to the **synthetic-data-evaluation** skill, which completes sections 7-10.
Required before the data is used in a demo or leaves the environment. That skill handles the
no-real-seed-data case where train-on-synthetic/test-on-real is impossible.
