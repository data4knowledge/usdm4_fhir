import re


def fix_uuid(text):
    refs = re.findall(
        r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}", text
    )
    seen = {}
    counter = 0
    for ref in refs:
        if ref not in seen:
            counter += 1
            seen[ref] = f"00000000-0000-4000-0000-{counter:012d}"
    for original, replacement in seen.items():
        text = text.replace(original, replacement)
    return text


def fix_iso_dates(text):
    dates = re.findall(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{6}[+-]\d\d:\d\d", text)
    for date in dates:
        text = text.replace(date, "2024-12-25T00:00:00.000000+00:00")
    dates = re.findall(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{6}Z", text)
    for date in dates:
        text = text.replace(date, "2024-12-25T00:00:00.000000+00:00")
    return text
