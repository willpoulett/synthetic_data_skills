"""Extract a machine-readable JSON schema from an NHS Technical Output Specification Excel file.

Generic: works with any NHS TOS Excel that follows the standard layout
(MSDS, HES, ECDS, etc.). Each MSD/HES-numbered tab becomes a table in the schema.

Usage:
    python scripts/extract_tos_schema.py path/to/TOS.xlsx --output schemas/msds_v2.0.31.json
    python scripts/extract_tos_schema.py path/to/TOS.xlsx --tables MSD001,MSD101,MSD301
"""

import argparse
import json
import re
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import openpyxl

sys.path.insert(0, str(Path(__file__).parent))
from format_parser import parse_format

UID_PATTERN = re.compile(r"^M\d{3,6}")

CODED_ENTRY_MARKERS = [
    "(CODED CLINICAL ENTRY)",
    "(SNOMED CT)",
    "(CLINICAL TERMINOLOGY)",
]

CODING_SCHEME_MAP = {
    "01": "ICD-10",
    "02": "ICD-10",
    "03": "Read v3 (CTV3)",
    "04": "Read v2",
    "05": "Read v3 (CTV3)",
    "06": "SNOMED CT",
}


def _is_uid(value):
    if value is None:
        return False
    return bool(UID_PATTERN.match(str(value).strip()))


def _str_or_none(value):
    if value is None:
        return None
    s = str(value).strip()
    return s if s else None


def _detect_coded_clinical_entry(name):
    if not name:
        return False
    upper = name.upper()
    return any(marker in upper for marker in CODED_ENTRY_MARKERS)


def _extract_table_id(sheet_name):
    """Extract the table ID prefix (e.g. 'MSD001') from the sheet name."""
    m = re.match(r"(MSD\d{3})", sheet_name)
    if m:
        return m.group(1)
    m = re.match(r"(HES\w+)", sheet_name)
    if m:
        return m.group(1)
    return sheet_name


def extract_table(ws, sheet_name):
    """Extract all fields from one TOS worksheet.

    Returns a dict with table metadata and fields keyed by xml_element_name.
    """
    display_name = _str_or_none(ws.cell(row=3, column=1).value) or sheet_name
    group_mandation = None
    mand_text = _str_or_none(ws.cell(row=3, column=14).value)
    if mand_text:
        for code in ("M", "R", "O"):
            if code in mand_text.split("\n")[0]:
                group_mandation = code
                break

    fields = {}
    current_field = None

    for row in range(1, ws.max_row + 1):
        uid_val = ws.cell(row=row, column=1).value
        name_val = ws.cell(row=row, column=2).value
        xml_val = ws.cell(row=row, column=3).value
        desc_val = ws.cell(row=row, column=4).value
        fmt_val = ws.cell(row=row, column=5).value
        code_val = ws.cell(row=row, column=6).value
        code_def = ws.cell(row=row, column=7).value
        mand_val = ws.cell(row=row, column=14).value

        if _is_uid(uid_val):
            uid = str(uid_val).strip()
            name = _str_or_none(name_val) or ""
            xml_element = _str_or_none(xml_val)
            description = _str_or_none(desc_val)
            fmt_raw = _str_or_none(fmt_val)
            mandation = _str_or_none(mand_val)

            deriv_val = ws.cell(row=row, column=16).value
            current_field = {
                "uid": uid,
                "data_item_name": name,
                "xml_element_name": xml_element,
                "description": description,
                "format_raw": fmt_raw,
                "format": parse_format(fmt_raw) if fmt_raw else None,
                "national_codes": None,
                "coded_clinical_entry": _detect_coded_clinical_entry(name),
                "mandation": mandation,
                "derivation_notes": _str_or_none(deriv_val),
            }

            if code_val is not None:
                current_field["national_codes"] = {
                    str(code_val): _str_or_none(code_def) or ""
                }

            key = xml_element or uid
            fields[key] = current_field

        elif code_val is not None and current_field is not None:
            if current_field["national_codes"] is None:
                current_field["national_codes"] = {}
            current_field["national_codes"][str(code_val)] = (
                _str_or_none(code_def) or ""
            )

    return {
        "sheet_name": sheet_name,
        "display_name": display_name,
        "group_mandation": group_mandation,
        "fields": fields,
    }


def extract_schema(xlsx_path, table_filter=None):
    """Extract a full schema from a TOS Excel file.

    Args:
        xlsx_path: path to the TOS .xlsx file
        table_filter: optional list of table IDs to include (e.g. ["MSD001", "MSD101"])

    Returns:
        dict with dataset metadata and tables.
    """
    path = Path(xlsx_path)

    # Copy to temp if the file might be locked (OneDrive)
    try:
        wb = openpyxl.load_workbook(str(path), data_only=True, read_only=True)
    except PermissionError:
        tmp = Path(tempfile.mkdtemp()) / path.name
        shutil.copy2(path, tmp)
        wb = openpyxl.load_workbook(str(tmp), data_only=True, read_only=True)

    dataset_name = ""
    version = ""
    filename = path.name
    m = re.search(r"(MSDS|HES|ECDS)", filename, re.IGNORECASE)
    if m:
        dataset_name = m.group(1).upper()
    m = re.search(r"v(\d+\.\d+[\.\d]*)", filename, re.IGNORECASE)
    if m:
        version = m.group(1)

    tables = {}
    for sheet_name in wb.sheetnames:
        table_id = _extract_table_id(sheet_name)
        if not re.match(r"MSD\d{3}|HES", table_id):
            continue
        if table_filter and table_id not in table_filter:
            continue

        ws = wb[sheet_name]
        tables[table_id] = extract_table(ws, sheet_name)

    wb.close()

    return {
        "dataset": dataset_name,
        "version": version,
        "source_file": filename,
        "extracted_at": datetime.now().isoformat(timespec="seconds"),
        "tables": tables,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Extract a JSON schema from an NHS TOS Excel file."
    )
    parser.add_argument("xlsx_path", help="Path to the TOS .xlsx file")
    parser.add_argument(
        "--output", "-o",
        help="Output JSON file path (default: schemas/<dataset>_v<version>.json)",
    )
    parser.add_argument(
        "--tables", "-t",
        help="Comma-separated table IDs to extract (default: all)",
    )
    args = parser.parse_args()

    table_filter = None
    if args.tables:
        table_filter = [t.strip() for t in args.tables.split(",")]

    schema = extract_schema(args.xlsx_path, table_filter)

    if args.output:
        out_path = Path(args.output)
    else:
        out_dir = Path(__file__).resolve().parent.parent / "schemas"
        out_dir.mkdir(exist_ok=True)
        name = schema["dataset"] or "unknown"
        ver = schema["version"] or "0"
        out_path = out_dir / f"{name.lower()}_v{ver}.json"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)

    n_tables = len(schema["tables"])
    n_fields = sum(len(t["fields"]) for t in schema["tables"].values())
    print(f"Extracted {n_tables} tables, {n_fields} fields -> {out_path}")


if __name__ == "__main__":
    main()
