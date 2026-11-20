import csv
from pathlib import Path

import pandas as pd

from db import get_engine

CSV_PATH = Path("data/raw/SR2025.csv")
TABLE = "sr_raw"
REJECT_TABLE = "sr_rejects"
BATCH_ROWS = 50_000
EXPECTED_FIELDS = 9
COLUMNS = [
    "creation_date", "status", "postal_prefix", "intersection_1", "intersection_2",
    "ward", "service_request_type", "division", "section", "source_file",
]


def repair(row):
    """The division 'Environment, Climate & Forestry' has an unquoted comma."""
    if (
        len(row) == EXPECTED_FIELDS + 1
        and row[7].strip() == "Environment"
        and row[8].strip() == "Climate & Forestry"
    ):
        return row[:7] + ["Environment, Climate & Forestry"] + row[9:]
    return row


engine = get_engine()
good, rejects = [], []
loaded = repaired = rejected = 0
first_good = first_reject = True


def flush_good():
    global good, first_good
    if good:
        df = pd.DataFrame(good, columns=COLUMNS)
        df.to_sql(TABLE, engine, if_exists="replace" if first_good else "append", index=False)
        first_good = False
        good = []


def flush_rejects():
    global rejects, first_reject
    if rejects:
        df = pd.DataFrame(rejects)
        df.to_sql(REJECT_TABLE, engine, if_exists="replace" if first_reject else "append", index=False)
        first_reject = False
        rejects = []


with open(CSV_PATH, newline="", encoding="cp1252") as f:
    reader = csv.reader(f)
    next(reader)  # skip the header row
    for record_number, row in enumerate(reader, start=2):
        fixed = repair(row)
        if fixed is not row:
            repaired += 1
        if len(fixed) == EXPECTED_FIELDS:
            good.append([v if v != "" else None for v in fixed] + [CSV_PATH.name])
            loaded += 1
        else:
            rejects.append(
                {"record_number": record_number, "field_count": len(row), "raw_text": ",".join(row)}
            )
            rejected += 1
        if len(good) >= BATCH_ROWS:
            flush_good()
            print(f"loaded {loaded} rows so far")

flush_good()
flush_rejects()
print(f"Done. loaded={loaded} repaired={repaired} rejected={rejected}")
