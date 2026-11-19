# Claude Instructions

## What this project is

An agentic proof-of-concept (PoC) generator for healthcare AI applications. Its job is to spin up realistic synthetic healthcare datasets across many modalities so that AI PoCs can be built and demonstrated without touching real patient data.

"Healthcare" here is deliberately broad: tabular EHR-style records, longitudinal patient pathways, clinical text, medical imaging, physiological signals and wearables, speech/audio, and genomics/omics.

## Core principles (these shape every decision)

Cross-modal / cross-record coherence is the priority. A synthetic patient is only useful if their genomics, labs, notes, wearable trends, and imaging tell the same clinical story. Independent per-modality generation that shares only a patient ID is not a synthetic patient — it is several unrelated files. When in doubt, favour coherence over per-modality fidelity.
Generation and evaluation are separate concerns. Every generated dataset should be evaluatable. Do not treat evaluation as an afterthought — see the synthetic-data-evaluation skill.
Guard against the label-validity trap. If synthetic data and the AI being demoed are both LLM-driven, a PoC can accidentally prove only that an LLM recognises its own output. Keep data generation and label generation distinct, and validate against real holdout data where it exists.
Privacy is load-bearing, not polish. This is healthcare. Synthetic data is not automatically private. Any dataset that may leave the environment must pass a privacy audit before it is shared.
Environment matters. The target environment (e.g. FDP) may not run every dependency. Prefer pure-Python, easy-to-install tools; flag anything needing Java, Julia, or pinned/complex environments before relying on it.

## Skills — read these rather than guessing

Two project skills in `.claude/skills/` encode the detailed, hard-won knowledge. Prefer them over memory; they are the source of truth for tool choices and methodology.

`synthetic-data-generation` — routes to the right tool for each modality (tabular, EHR/pathways, clinical text, signals/wearables, audio/speech, genomics, and the "generate from intelligence / no seed data" case). Use this whenever the task is to produce synthetic data.
`synthetic-data-evaluation` — the fidelity / utility / privacy framework, including TSTR methodology, clinical-plausibility checks, and privacy auditing. Use this whenever the task is to assess synthetic data, and after generating any dataset.

Each skill is a lean router `SKILL.md` plus a `references/` folder holding the depth. Read the one or two reference files the task needs, not the whole set — that is the point of the structure. Reference files are written terse, for an agent to act on. Keep them that way.

Every generated dataset gets a `REPORT.md` written alongside the data: provenance (sections 1–6, written during generation) and evaluation (sections 7–10). Template and rules are in `synthetic-data-evaluation/references/report.md`. There are no numeric pass/fail thresholds — none has been agreed, so the report states what was measured, what was not, and why.

These two are intended to work together: generated data should be run through evaluation, and evaluation must account for the "no real seed data" case where train-on-synthetic/test-on-real is not possible.

Two things the skills deliberately do not cover:

- **Medical imaging is not supported.** There is not enough assessed material to route on, so there is no imaging reference file. The generation `SKILL.md` records what was assessed (medigan, MONAI, RoentMod — all GPU-gated, FDP feasibility unknown) and instructs: confirm the approach with the user before promising imaging output. Do not fill this gap from memory.
- **No evaluation scripts exist yet.** `references/fidelity.md` and `references/utility.md` name the two that should eventually live under the skill — a clinical-plausibility rule checker and a TSTR harness — with their intended interfaces. Build them when a real dataset needs them, not speculatively.

The tools tables in the reference files are the sanctioned inventory — they are the authority for *which* tools may be recommended. They were built from an asset audit and corrected against the asset repositories (read 2026-07-29), and they carry licences, dependencies, verdicts and read dates.

Rules:

- **Recommend only what is listed.** Adding a tool requires user approval and a source URL recorded in the table. Never add one from memory, however plausible.
- **A primary source beats an older assessment** on setup, dependencies, licence, method and maintenance, provided the entry records the URL and the date read. Three such corrections are already in place: SynPath, SCN and TAPAS are all pip-installable Python, against an earlier "hard to set up" / "no setup notes".
- **Nothing here has been verified by running it.** Repository claims are still claims. Install before committing to a tool.

Assets marked "inspiration" get an entry in the relevant reference file: source and date read, the pattern, what to copy, what to substitute, what not to inherit, and caveats. Take the approach, not the toolchain — an LLM call often replaces a specialist library with nothing to install. Ask the user or fetch the source when an entry is insufficient, but never make a network fetch a dependency of a method; the target environment may have no outbound access.

## Collaboration with user

Ask questions often when instructions are unclear.
When coding, if making a decision that will change the behaviour of the tool and was not discussed with the user, ask the user to clarify.

## When unsure

For tool selection or generation method → consult the synthetic-data-generation skill and its reference files.
For "is this good / safe enough?" → consult the synthetic-data-evaluation skill.
For anything that would touch real data, privacy, or leaves the environment → stop and confirm rather than assume.

## Learning loop

When a dataset generation or evaluation is complete, capture learnings that would help a future user working with the same or similar datasets:

- **Generic findings** (apply to any dataset) → update the relevant SKILL.md (generation or evaluation)
- **Dataset-specific findings** (conditional sampling chain, NULL fields, known pitfalls, external references) → update or create a reference file under `references/` in the relevant skill. One file per dataset or dataset family. Use the existing `references/msds.md` and `references/pathways.md` as templates.
- **What tripped up the AI** is the highest-value learning. Record it: the mistake, the root cause, and the fix.
- If a Confluence learnings page exists for this work, update it too.

Each dataset reference file should include: what the dataset is, the conditional sampling chain, what worked, what tripped up the AI, external references used, and evaluation checks specific to that dataset.

## Scope

- Only read, write, or reference files within this repository.
- Do not access, read, or write files in `/tmp`, `~/`, or any path outside this repository.
- Do not make network requests (curl, wget, web fetch) unless explicitly asked.

## Tool usage

- Use `Read`, `Grep`, and `Glob` directly for simple file searches. Only spawn an Explore or general-purpose agent when those tools are clearly insufficient.
- Do not use a subagent (Task tool) to read binary files (e.g. `.xlsx`, `.pdf`, `.parquet`). Instead, read them in-process via Bash with `openpyxl`/`polars`/`pandas`, or ask the user to provide the relevant content as text.
- Do not write to `/tmp` or use shell commands that expand outside the repo.

## Reusable scripts

`scripts/extract_tos_schema.py` — parses any NHS TOS Excel into a JSON schema (MSDS, MHSDS, HES, ECDS, CSDS, IAPT). Use it before generating any TOS-defined dataset. Captures field names, data types, mandation levels, national codes, and derivation notes.

`scripts/format_parser.py` — parses NHS TOS format notation (e.g. `an10 CCYY-MM-DD`, `max n20`) into structured validation rules. Used by the schema extractor.

Dataset-specific scripts (generators, evaluators, distribution files) are written per-project and not committed — the patterns they follow are documented in the skills and reference files.

## Generated data

Generated CSV data is not committed to this repo. Each generation run writes to `data/{dataset}_{fidelity}/` locally. The `data/broken_arm_day1/` demo dataset is the exception — it is committed as a curated example.

## Python

- The virtual environment is at `.venv/`. You may need to create this.

## Git

- Do not commit or push unless explicitly asked.
- Do not use `--no-verify`, `--force`, or `git reset --hard` without explicit user instruction.

## Code style

- Do not over-engineer: no helpers for one-off operations, no backwards-compatibility shims. Code should be as simple as possible.