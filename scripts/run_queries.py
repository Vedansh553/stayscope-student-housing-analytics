"""Run every SQL file in sql/queries/, print a preview, and export CSVs for Power BI / Tableau."""
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
con = sqlite3.connect(ROOT / "data" / "stayscope.db")
out = ROOT / "exports"
out.mkdir(exist_ok=True)

pd.set_option("display.width", 200, "display.max_columns", 20)
for f in sorted((ROOT / "sql" / "queries").glob("*.sql")):
    df = pd.read_sql_query(f.read_text(), con)
    df.to_csv(out / f"{f.stem}.csv", index=False)
    print(f"\n=== {f.stem}  ({len(df)} rows) ===")
    print(df.head(12).to_string(index=False))
