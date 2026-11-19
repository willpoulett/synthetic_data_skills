# NHS TOS-based datasets

## Applies to

Any NHS dataset defined by a Technical Output Specification (TOS): MSDS, MHSDS, HES, ECDS, CSDS,
IAPT, CDS, and similar. Read this when generating synthetic data for a TOS-defined dataset.

## TOS interpretation

The TOS Excel defines every field: name, data type, mandation level, description, national code
list, and derivation notes. Two columns matter most and are routinely confused:

- **Description (column 4)** — what the field IS. Reads like it needs a value.
- **Derivation notes (column 16)** — whether it CURRENTLY has a value. This is the authority.

Many fields have plausible descriptions but derivation notes saying "At present this derivation
will always be NULL." The AI will populate these every time unless explicitly told not to.

**Parse the TOS into machine-readable format (JSON) first**, including derivation notes for every
field. This is the single most effective step to prevent field-level bugs.

## Mandation levels

Three levels: **M** (Mandatory), **R** (Required), **D** (Derived).

Every field in the TOS must appear as a column in the output, regardless of mandation level.
Mandation determines whether the value must be non-null, not whether the column exists. The MSDS
TOS has 197 D fields across 10 tables — all must be present as columns.

## Derived field categories

D fields are not uniform. For MSDS they fall into 6 categories (counts will differ per dataset but
the categories transfer):

| Category | MSDS count | Handling | Examples |
| --- | --- | --- | --- |
| **Boilerplate** | 80 | Generate with synthetic values. Every table has: ID, OrgCodeProvider, RecordNumber, Person_ID, RPStartDate/RPEndDate, Effective_From | MSD001_ID, RPStartDate |
| **Derivable from state** | 27 | Compute from existing data. Ages from DOB+event date. Gestational age from LMP. Validation flags from NHS number/postcode validity | AgeAtBookingMother, ValidNHSNoFlagMother |
| **Clinically meaningful** | 15 | Check derivation notes — most say "always NULL" despite being real clinical concepts | SmokingStatusBooking (NULL), RobsonGroup (NULL), PersonBMIBand (NULL) |
| **Geographic** | 9 | Postcode district from postcode. LSOA, LAD, IMD require lookup tables — NULL unless provided | PostcodeDistrictMother, LSOAMother2011 |
| **Code mappings** | 48 | All NULL — system-level crosswalks (SNOMED↔ICD-10↔OPCS-4) the submission portal derives | MasterSnomedCTDiagCode, MapICD10Code |
| **Commissioning** | 8 | All NULL — TOS notes describe these as "placeholder derivation" | OrgCodeAPLC, OrgIDPostPathICB |

## Specific NULL fields (MSDS v2.0.31)

These all say "At present this derivation will always be NULL" in column 16. Columns must exist
but be empty:

- SmokingStatusBooking, SmokingStatusDelivery, SmokingStatusDischarge
- PersonBMIBooking, PersonBMIBand, DerivedBMI
- RobsonGroup
- BirthWeight (as D column in MSD405)
- All Map* code mapping fields
- All MasterICD10*, MasterOPCS4* fields
- All commissioning placeholders (OrgCodeAPLC, OrgCodePPLC, ICB/SubICB variants)

Note: the smoking_status value may still be useful internally for conditional sampling (smoking
affects pregnancy outcomes) but must NOT be written to the SmokingStatus columns.

## Fields with actual derivation logic (not "always NULL")

- BirthsPerLabandDel — count of MSD401 records per labour/delivery
- ApgarScore — if observation code = 169909004, use ObsValue
- Age derivations — from DOB + event date
- Gestational age derivations — from LMP/EDD + event date
- Date decompositions (Year/Month/Day/Meridian of birth/death)
- Validation flags (ValidNHSNoFlagMother/Baby, ValidPostcodeFlag)
- PostcodeDistrictMother — from postcode (if valid)

## Field naming

Column names must match the TOS `field_name` (or `xml_element_name`) exactly,
character-for-character. Case-sensitive. Mismatches cause schema validation failures and break
downstream pipelines.

## National Codes

For categorical fields with a defined National Code list, ONLY values from that list are valid.
Codes are strings, not integers — "01" ≠ 1, "2B" ≠ 28.

Known past bugs from MSDS:
- DischReason "10" (invalid) → should be "01" or "07"
- AdmMethCode "28" → should be "2B"
- AdmMethCode "32" → should be "2A"

## Coded Clinical Entry fields

Fields with "(CODED CLINICAL ENTRY)" in the TOS data item name require clinical codes:
- Check `coded_clinical_entry: true` in the parsed schema
- Use the coding scheme from the National Code column (ICD-10 or SNOMED-CT)
- SNOMED: use realistic concept IDs from the relevant refset
- ICD-10: use codes from the relevant chapter

## NHS number test range

Synthetic NHS numbers must use the 999 test range (starting with 999). These are structurally
impossible to collide with real patient numbers. This is a hard requirement for from-intelligence
generation where no IG approval exists.

## Evaluation note

When evaluating NHS TOS datasets, L0 schema checks must verify all three mandation levels.
See `synthetic-data-evaluation` SKILL.md, Step 4. The generation skill's
`references/nhs-datasets.md` (this file) documents what each D field category should contain.

## Report

Contributes to report sections 3 (field coverage by mandation level) and 4 (TOS version, schema
parser used, derivation notes coverage).
