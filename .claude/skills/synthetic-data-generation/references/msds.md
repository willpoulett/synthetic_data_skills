# MSDS (Maternity Services Data Set)

## What this dataset is

MSDS v2.0 is the national maternity dataset collected by NHS England. It covers the full maternity
pathway from booking to postnatal discharge. Defined by a TOS (Technical Output Specification)
with 31 tables and ~500+ fields across mandation levels M, R, and D.

Related datasets sharing the TOS structure: MHSDS, CSDS, IAPT, ECDS, HES. The generic TOS
guidance in `nhs-datasets.md` applies to all of them; this file covers MSDS-specific knowledge.

## Read first

- `nhs-datasets.md` — TOS interpretation, mandation levels, D-field categories, field naming,
  National Codes, NHS 999 test range
- `from-intelligence.md` — if generating without real seed data
- `tabular.md` — tool inventory for tabular generation

## Ordered conditional sampling chain

Dependencies must be sampled in this order. Breaking the order produces incoherent records (e.g.
elective CS onset with vaginal delivery — observed at 13.5% in low-fidelity independent sampling).

```
age → parity → BMI → GDM → gestation → presentation → delivery method → onset of labour → outcome → babies
```

Each stage conditions on previous stages:
- Parity distribution shifts with age (younger mothers more likely nulliparous)
- BMI affects GDM risk
- GDM affects gestation (earlier induction)
- Presentation affects delivery method (breech → higher CS rate)
- Delivery method constrains onset (elective CS has no spontaneous onset)
- Outcome cascades to baby records (stillbirth → Apgar=0, no breastfeeding, no skin-to-skin)

## Rare event cascades

These must propagate correctly through all downstream fields:

- **Stillbirth**: outcome code, Apgar=0, no breastfeeding initiation, no skin-to-skin, matching
  baby status, no neonatal admission
- **Neonatal death**: live birth initially, then death record with timing
- **Maternal death**: death record, all subsequent contacts absent
- **Pre-eclampsia**: affects delivery timing, method, and baby outcomes
- **GDM**: earlier induction, increased monitoring contacts
- **PPH**: affects postnatal care intensity

## MSDS-specific NULL fields (v2.0.31)

These all say "At present this derivation will always be NULL" in TOS column 16. Columns must
exist but be empty:

- SmokingStatusBooking, SmokingStatusDelivery, SmokingStatusDischarge
- PersonBMIBooking, PersonBMIBand, DerivedBMI
- RobsonGroup
- BirthWeight (as D column in MSD405 — the observation value in MSD109 is populated)
- All Map* code mapping fields (system-level SNOMED↔ICD-10↔OPCS-4 crosswalks)
- All MasterICD10*, MasterOPCS4* fields
- All commissioning placeholders (OrgCodeAPLC, OrgCodePPLC, ICB/SubICB variants)

Note: `smoking_status` may still be useful internally for conditional sampling (smoking affects
pregnancy outcomes) but must NOT be written to the SmokingStatus columns.

## Fields with actual derivation logic

Not all D fields are NULL. These have real computation rules:

- BirthsPerLabandDel — count of MSD401 records per labour/delivery
- ApgarScore — if observation code = 169909004, use ObsValue
- Age derivations (AgeAtBookingMother, AgeAtLabourMother, etc.) — from DOB + event date
- Gestational age derivations — from LMP/EDD + event date
- Date decompositions (Year/Month/Day/Meridian of birth/death)
- Validation flags (ValidNHSNoFlagMother/Baby, ValidPostcodeFlag)
- PostcodeDistrictMother — from postcode (if valid)
- MasterSnomedCT*Code — conditional on coding scheme being SNOMED (06)

## What tripped up the AI

| Issue | Root cause | Fix |
| --- | --- | --- |
| 197 D columns missing from output | Generator only produced M+R fields | Generate ALL columns regardless of mandation level |
| SmokingStatus populated when it should be NULL | Description says "derived smoking status where recorded at..." which looks like it needs a value | Derivation notes say "always NULL" — derivation notes win |
| RobsonGroup populated | Well-defined clinical classification (groups 1-10) but TOS says "always NULL" | Check derivation notes, not clinical knowledge |
| DischReason "10" invalid | Wrong National Code | Only "01" and "07" are valid |
| AdmMethCode "28", "32" invalid | Codes are strings not integers | Should be "2B" and "2A" |
| 13.5% elective CS onset with vaginal delivery | Independent sampling of onset and delivery method | Ordered conditional sampling: delivery method constrains onset |
| Home birth code "04" in non-home settings | Set membership shadowing in care setting logic | Exclude "04" from non-home-birth care settings |

## External references used

- **MSDS TOS v2.0.31**: `MSDS+v2.0+TOS+v2.0.31_15022023.xlsx`
- **Parsed schema**: `schemas/msds_v2.0.31.json`
- **NHS Maternity Statistics**: Published by NHS England — marginal distributions
- **ONS birth data**: Gestational age, birth weight, preterm rate
- **NICE NG201**: Antenatal care guideline — contact scheduling (10 contacts nulliparous,
  7 multiparous)
- **NMPA (National Maternity and Perinatal Audit)**: CS rate analysis
- **MBRRACE-UK**: Outcomes by ethnicity — relevant for fairness checks

## Evaluation checks specific to MSDS

- L0: all 3 mandation levels produce columns; D-field NULL/populated status matches derivation
  notes
- L1: marginals checked against NHS Maternity Statistics (delivery method, gestation distribution,
  age distribution, ethnicity, parity)
- L2: conditional distributions (delivery method given presentation, gestation given GDM,
  outcome given delivery method)
- L3: no pregnant males, plausible medication-condition pairings, Apgar scores consistent with
  outcome, contact scheduling follows NICE NG201 pattern
- P-value thresholds used: most checks p > 0.01 → PASS; delivery method (high DOF) p > 0.001 →
  PASS; correlations r > 0.1 and p < 0.05 → PASS
