"""Parse NHS TOS format notation into structured validation rules.

NHS Technical Output Specifications use a compact notation for field formats:
  an10 CCYY-MM-DD   → date
  an8 HH:MM:SS      → time
  max an20           → alphanumeric, up to 20 chars
  min an3 max an5    → alphanumeric, 3-5 chars
  n10                → numeric, exactly 10 digits
  min n6 max n18     → numeric, 6-18 digits

This module translates that notation into dicts usable by the validator.
"""

import re


def parse_format(fmt_str):
    """Parse an NHS format string into a structured dict.

    Returns a dict with keys:
        type: "date" | "time" | "datetime" | "alphanumeric" | "numeric" | "decimal" | "unknown"
        min_length: int or None
        max_length: int or None
        exact_length: int or None
    """
    if not fmt_str or not isinstance(fmt_str, str):
        return {"type": "unknown"}

    fmt = fmt_str.strip()

    if "CCYY-MM-DD" in fmt and "HH:MM:SS" in fmt:
        return {"type": "datetime"}

    if "CCYY-MM-DD" in fmt:
        return {"type": "date"}

    if "HH:MM:SS" in fmt:
        return {"type": "time"}

    # Decimal: "n10.n2", "max n20.max n2", "max n20. max n2"
    m = re.match(r"(?:max\s+)?n(\d+)\.\s*(?:max\s+)?n(\d+)", fmt, re.IGNORECASE)
    if m:
        return {
            "type": "decimal",
            "int_digits": int(m.group(1)),
            "dec_digits": int(m.group(2)),
        }

    # Range with min and max: "min an3 max an5" or "min n6 max n18"
    m = re.match(r"min\s+(a?n?)(\d+)\s+max\s+(a?n?)(\d+)", fmt, re.IGNORECASE)
    if m:
        typ = "alphanumeric" if "a" in m.group(1).lower() else "numeric"
        return {
            "type": typ,
            "min_length": int(m.group(2)),
            "max_length": int(m.group(4)),
        }

    # "max an20" or "max n3"
    m = re.match(r"max\s+(a?n?)(\d+)", fmt, re.IGNORECASE)
    if m:
        typ = "alphanumeric" if "a" in m.group(1).lower() else "numeric"
        return {"type": typ, "max_length": int(m.group(2))}

    # Fixed length: "an2", "n10", "an1"
    m = re.match(r"(a?n)(\d+)$", fmt, re.IGNORECASE)
    if m:
        typ = "alphanumeric" if "a" in m.group(1).lower() else "numeric"
        return {"type": typ, "exact_length": int(m.group(2))}

    # Numeric range for scores: "0-12", "0-2"
    m = re.match(r"(\d+)-(\d+)$", fmt)
    if m:
        return {
            "type": "numeric_range",
            "min_value": int(m.group(1)),
            "max_value": int(m.group(2)),
        }

    return {"type": "unknown", "raw": fmt}
