# Synthetic Data Skills

An agentic toolkit for generating and evaluating synthetic healthcare data. Built for use with Claude Code — the skills, reference files, and reusable scripts encode hard-won methodology so an AI assistant can produce realistic synthetic datasets without touching real patient data.

## How it works

Two Claude Code skills in `.claude/skills/`:

- **synthetic-data-generation** routes by modality (tabular, EHR, clinical text, signals, audio, genomics) and seeding case (real data, schema only, from intelligence). Reference files in `references/` hold tool inventories, method detail, and dataset-specific guidance.
- **synthetic-data-evaluation** assesses fidelity (does it look real), utility (is it useful), and privacy (does it leak). Runs after every generation.

Each generated dataset gets a `REPORT.md` written alongside the data covering provenance, cohort definition, evaluation results, and a privacy verdict.

## Getting started

```bash
python -m venv .venv
.venv/Scripts/activate   # Windows
pip install -r requirements.txt
```

Point Claude Code at this directory and describe what you need: "Generate 5,000 synthetic MSDS maternity records at medium fidelity" or "Create a synthetic A&E dataset from the ECDS TOS."

The skills guide the workflow. You provide the technical specification, published statistics, and clinical guidelines; the AI handles schema parsing, state sampling, generation, and evaluation.

## Directory structure

```
.claude/skills/
  synthetic-data-generation/    # Generation skill + references per modality/dataset
  synthetic-data-evaluation/    # Evaluation skill + references (fidelity, utility, privacy, report)
scripts/                        # Reusable scripts (schema extraction, LLM calls, checks)
schemas/                        # Machine-readable schemas extracted from specifications
data/                           # Generated datasets (each with its own REPORT.md)
```

## Reusable scripts

| Script | Purpose |
|--------|---------|
| `scripts/extract_tos_schema.py` | Parse any NHS Technical Output Specification Excel into a JSON schema. Works with MSDS, MHSDS, HES, ECDS, CSDS, IAPT. |
| `scripts/format_parser.py` | Parse NHS TOS format notation (`an10 CCYY-MM-DD`, `max n20`) into structured validation rules. |
| `scripts/call_llm.py` | LLM entry point for Foundry-hosted models. Use for free-text fields, not for patient state sampling. |

## Workflow summary

1. **Agree scope** — dataset, fidelity tier, tables, record count, seeding case
2. **Parse specification** — extract to machine-readable schema with all metadata columns
3. **Write data specification** — cohort definition, distribution targets, all numbers sourced
4. **Sample patient state** — seeded RNG, ordered conditional sampling, labels before content
5. **Generate** — every table from the shared state, column counts verified against spec
6. **Evaluate** — schema conformance, distribution checks, clinical plausibility, privacy
7. **Report** — REPORT.md sections 1-10 written alongside the data

## Contributing learnings

When you complete a dataset generation, capture what you learned — see the learning loop guidance in `CLAUDE.md`. Generic findings update the skills; dataset-specific findings go in reference files.
