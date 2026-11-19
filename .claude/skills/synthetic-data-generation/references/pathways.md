# NHS Pathways (Triage Data)

## What this dataset is

NHS Pathways triage data records telephone and online triage interactions — the decision support
system used by NHS 111, 999, and some Clinical Assessment Services. Each record captures the
patient's demographics, presenting complaint, the symptom group assessed, the triage disposition
(outcome), timing, and clinician involvement.

This is not a TOS-defined dataset. It has its own schema but shares some principles with TOS
datasets (National Codes, coded fields, standardised dispositions).

## Read first

- `from-intelligence.md` — if generating without real seed data
- `tabular.md` — tool inventory for tabular generation

## Ordered conditional sampling chain

```
service_type → age → gender → symptom_group → disposition_category → Dx_code → timestamps → clinician_involvement
```

Each stage conditions on previous stages:
- Service type (111 vs 999 vs CAS) determines the distribution of symptom groups and dispositions
- Age affects which symptom groups appear (paediatric vs adult presentations)
- Symptom group constrains which disposition categories are possible
- Disposition category determines the specific Dx code
- Timestamps depend on service type (999 calls shorter than 111) and disposition (ambulance
  dispatch faster than GP referral)
- Clinician involvement depends on disposition category and service type

## Algebraic decomposition for service-specific distributions

Published statistics are often aggregated across all service types. When generating per-service-type
records, you need to decompose the aggregate:

```
service_specific_rate = (published_total - sum_of_other_services) / service_volume
```

Do not use published aggregate rates directly as parameters for a single service type — the
aggregate is a weighted average across services with different case mixes.

Example: if the published overall ambulance dispatch rate is 10%, but 999 dispatches at 30% and
111 at 5%, using 10% for both services produces unrealistic data.

## Triage-portion modelling for call duration

Call duration has a triage portion (time spent in the Pathways algorithm) and a non-triage portion
(wrap-up, handover, waiting). Published mean call duration includes both. The triage portion is
what varies with symptom complexity; the non-triage portion is roughly constant.

```
triage_duration = f(symptom_group, disposition)  # varies
non_triage_duration ~ constant + noise            # roughly fixed
total_duration = triage_duration + non_triage_duration
```

Using published total duration directly as the parameter for a single phase produces durations that
are too long for simple cases and too short for complex ones.

## Set membership shadowing (the Repeat Prescription bug)

if/elif chains where a general category matches before a specific one, so correctly-coded
specific-case fixes never fire:

```python
# WRONG — "Repeat Prescription" is a subcategory of "Pharmacy"
if symptom_group in PHARMACY_GROUPS:
    disposition = sample_pharmacy_disposition()
elif symptom_group == "Repeat Prescription":
    disposition = sample_repeat_rx_disposition()  # never reached
```

Check specific-before-general ordering in every conditional adjustment. This bug is silent — the
code runs without error, the general distribution looks plausible, but the specific subcategory
has the wrong distribution.

## Structurally absent categories (the "Unknown" disposition problem)

Some categories exist in published statistics but cannot be generated from the conditional sampling
chain:

- "Unknown" disposition: published stats report ~X% unknown, but the sampling chain always produces
  a known disposition. You must explicitly inject unknowns after sampling.
- "No outcome recorded": similarly absent from a clean sampling chain.

Check the published distribution for categories that the generator structurally cannot produce, and
add explicit injection steps for them.

## Marginal distribution shifts from fixes

Each fix to a conditional distribution shifts the overall marginal. Example: fixing the Repeat
Prescription disposition (above) increases the count of a specific disposition category, which
shifts the overall disposition distribution away from the published target.

**Re-check overall marginals after every batch of fixes.** The process is iterative:
fix a conditional → check the marginal → adjust if needed → check conditionals again.

## What tripped up the AI

| Issue | Root cause | Fix |
| --- | --- | --- |
| Repeat Prescription dispositions wrong | Set membership shadowing — general pharmacy category matched before specific subcategory | Reorder if/elif to check specific before general |
| "Unknown" disposition missing | Sampling chain always produces a known outcome | Explicitly inject unknowns at published rate after sampling |
| 999 call durations too long | Used aggregate duration (including 111) as 999 parameter | Algebraic decomposition: isolate 999-specific duration |
| Marginal distribution drifted after conditional fixes | Each fix shifts the overall marginal | Re-check marginals after every batch of fixes |
| Service-type-specific rates wrong | Used published aggregate rates for individual services | Decompose published aggregates before using as per-service parameters |

## External references used

- NHS Pathways documentation and disposition code lists
- NHS 111 Minimum Data Set specification
- Published 111/999 activity statistics (NHS England)
- Disposition category definitions and Dx code mappings

## Evaluation checks specific to Pathways

- L0: all fields present, disposition codes valid, Dx codes match their disposition category
- L1: service type distribution, symptom group frequencies, disposition distribution vs published
  stats
- L2: conditional distributions (disposition given service type, duration given symptom complexity,
  clinician involvement given disposition)
- L3: no impossible symptom-disposition combinations, call durations within plausible ranges,
  timestamps in correct order (call start < triage start < triage end < call end)
