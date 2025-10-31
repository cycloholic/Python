# csv_reader.py
from __future__ import annotations
import csv, io, requests
from typing import List, Dict, Tuple

def fetch_csv(url: str) -> Tuple[List[str], List[Dict[str, str]]]:
    """
Downloads the CSV and returns header + row data as dictionaries.

- Uses ';' as delimiter and '"' as quote character  
- Supports newlines inside quoted fields (e.g. long HTML descriptions)  
- If a row has more fields than expected, extra values are merged into the last column  
  (this usually happens in the description field where HTML or text can contain commas/semicolons)
"""

    r = requests.get(url, timeout=30)
    r.raise_for_status()
    text = r.content.decode("utf-8", errors="replace")
    buf = io.StringIO(text)

    # header
    header_line = buf.readline().rstrip("\n")
    headers = next(csv.reader([header_line], delimiter=';', quotechar='"'))
    expected = len(headers)

    rows: List[Dict[str, str]] = []
    reader = csv.reader(buf, delimiter=';', quotechar='"')
    for row in reader:
        if len(row) > expected:
            row = row[: expected - 1] + [';'.join(row[expected - 1:])]
        elif len(row) < expected:
            row = row + [''] * (expected - len(row))
        item = {headers[i]: row[i] for i in range(expected)}  
        rows.append(item)
    return headers, rows
