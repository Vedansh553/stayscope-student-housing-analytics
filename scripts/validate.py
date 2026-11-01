"""
Validation harness: never trust a number (AI-written or hand-written) until it has been
re-derived a second way.

Three layers:
  1. DATA QUALITY   - keys, orphans, ranges, logical date order, double-booking
  2. RECONCILIATION - SQL results vs an independent pandas recomputation from raw tables
  3. PATTERN CHECKS - do the analyses recover the patterns planted by the generator?

Writes docs/validation_report.md and exits non-zero if any check fails.
"""
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
con = sqlite3.connect(ROOT / "data" / "stayscope.db")
T = {t: pd.read_sql_query(f"SELECT * FROM {t}", con) for t in
     ["cities", "universities", "properties", "units", "students", "leads", "bookings", "payments", "reviews"]}
Q = {f.stem: pd.read_sql_query(f.read_text(), con) for f in sorted((ROOT / "sql" / "queries").glob("*.sql"))}

results = []


def check(layer, name, ok, detail=""):
    results.append((layer, name, bool(ok), detail))


# ------------------------------------------------------------------ 1. DATA QUALITY
for table, pk in [("cities", "city_id"), ("properties", "property_id"), ("units", "unit_id"),
                  ("leads", "lead_id"), ("bookings", "booking_id"), ("payments", "payment_id"), ("reviews", "review_id")]:
    check("Data quality", f"{table}.{pk} unique & non-null", T[table][pk].is_unique and T[table][pk].notna().all())

fks = [("properties", "city_id", "cities"), ("units", "property_id", "properties"),
       ("leads", "city_id", "cities"), ("bookings", "lead_id", "leads"), ("bookings", "unit_id", "units"),
       ("payments", "booking_id", "bookings"), ("reviews", "booking_id", "bookings")]
for child, col, parent in fks:
    pk = T[parent].columns[0]
    orphans = (~T[child][col].isin(T[parent][pk])).sum()
    check("Data quality", f"No orphan {child}.{col} -> {parent}", orphans == 0, f"{orphans} orphans")

b = T["bookings"].copy()
b["booked_at"], b["start_date"] = pd.to_datetime(b.booked_at), pd.to_datetime(b.start_date)
b["end_date"] = [s + pd.DateOffset(months=int(m)) for s, m in zip(b.start_date, b.duration_months)]
lead_created = T["leads"].set_index("lead_id")["created_at"].pipe(pd.to_datetime)
check("Data quality", "booked_at >= lead created_at", (b.booked_at >= b.lead_id.map(lead_created)).all())
check("Data quality", "start_date after booked_at", (b.start_date > b.booked_at).all())

# double-booking guard (all bookings, incl. cancelled, were generated non-overlapping)
overlaps = 0
for _, g in b.sort_values("start_date").groupby("unit_id"):
    ends = g.end_date.to_numpy()
    starts = g.start_date.to_numpy()
    overlaps += int((starts[1:] < ends[:-1]).sum())
check("Data quality", "No double-booked units", overlaps == 0, f"{overlaps} overlaps")

check("Data quality", "leads.converted == presence of a booking",
      set(T["leads"].loc[T["leads"].converted == 1, "lead_id"]) == set(b.lead_id))
rent_match = b.merge(T["units"], on="unit_id", suffixes=("", "_u"))
check("Data quality", "booking rent == unit rent (snapshot)", np.allclose(rent_match.monthly_rent_usd, rent_match.monthly_rent_usd_u))
ok_pay = T["payments"].groupby("booking_id")["status"].apply(lambda s: (s == "Success").sum() <= 1)
check("Data quality", "<= 1 successful payment per booking", ok_pay.all())
rev_ok = T["reviews"].merge(b[["booking_id", "status"]], on="booking_id")
check("Data quality", "Reviews only on Completed bookings", (rev_ok.status == "Completed").all())

# ------------------------------------------------------------------ 2. RECONCILIATION
live = b[b.status.isin(["Confirmed", "Completed"])].copy()
live["gmv"] = live.monthly_rent_usd * live.duration_months
live["month"] = live.booked_at.dt.strftime("%Y-%m")

pd_month = live.groupby("month").agg(bookings=("booking_id", "count"), gmv=("gmv", "sum"))
q1 = Q["01_monthly_gmv_mom"].set_index("month")
check("Reconciliation", "Q01 monthly bookings match pandas", (q1.bookings == pd_month.bookings.reindex(q1.index)).all())
check("Reconciliation", "Q01 monthly GMV matches pandas (±$1 rounding)",
      np.allclose(q1.gmv_usd, pd_month.gmv.reindex(q1.index).round(0), atol=1))
check("Reconciliation", "Q01 total GMV == pandas total", abs(q1.gmv_usd.sum() - live.gmv.sum()) < len(q1))
q10 = Q["10_cumulative_and_rolling"]
# Compare to the exact unrounded total from raw rows (Q01's months are each rounded to $1, so summing
# them would drift by up to ~$0.5 per month - a validator bug I hit and fixed, see docs/ai_mistakes_log.md).
check("Reconciliation", "Q10 final cumulative GMV == exact raw total (±$1)", abs(q10.cumulative_gmv_usd.iloc[-1] - live.gmv.sum()) <= 1)

q2 = Q["02_funnel_by_city"]
check("Reconciliation", "Q02 leads sum == leads table rows", q2.leads.sum() == len(T["leads"]))
check("Reconciliation", "Q02 bookings sum == bookings table rows", q2.bookings.sum() == len(b))
check("Reconciliation", "Q02 visits sum == SUM(leads.visited)", q2.visits.sum() == T["leads"].visited.sum())

q3 = Q["03_response_time_vs_conversion"]
check("Reconciliation", "Q03 buckets cover every lead exactly once", q3.leads.sum() == len(T["leads"]))

q4 = Q["04_cancellation_by_source"]
bl = b.merge(T["leads"][["lead_id", "source"]], on="lead_id")
pd_cancel = bl.groupby("source").apply(lambda g: (g.status == "Cancelled").mean() * 100, include_groups=False)
check("Reconciliation", "Q04 cancel rate matches pandas",
      np.allclose(q4.set_index("source").cancel_rate_pct, pd_cancel.reindex(q4.source).round(1).to_numpy(), atol=0.06))

q5 = Q["05_payment_failure_by_method"]
check("Reconciliation", "Q05 first attempts == number of bookings", q5.first_attempts.sum() == len(b))

# Q07: recompute occupied units for two city-months independently
uc = T["units"].merge(T["properties"][["property_id", "city_id"]], on="property_id")
q7 = Q["07_occupancy_by_city_month"]
rng = np.random.default_rng(7)
sample = q7.sample(8, random_state=7)
mism = 0
for r in sample.itertuples():
    m0 = pd.Timestamp(r.month + "-01")
    m1 = m0 + pd.DateOffset(months=1)
    cities = T["cities"].set_index("city")["city_id"]
    cid = cities[r.city]
    units_in_city = set(uc.loc[uc.city_id == cid, "unit_id"])
    act = live[(live.start_date < m1) & (live.end_date > m0) & (live.unit_id.isin(units_in_city))]
    mism += int(act.unit_id.nunique() != r.occupied_units)
check("Reconciliation", "Q07 occupied units match pandas (8 random city-months)", mism == 0, f"{mism} mismatches")

# ------------------------------------------------------------------ 3. PATTERN CHECKS
q3s = q3.sort_values("response_bucket")
check("Pattern", "P2 booking rate falls as response time rises", q3s.booking_rate_pct.is_monotonic_decreasing)
check("Pattern", "P3 Aggregator has the highest cancellation rate", q4.sort_values("cancel_rate_pct").source.iloc[-1] == "Aggregator")
check("Pattern", "P4 Bank Transfer has the highest first-try failure", q5.sort_values("first_try_fail_pct").method.iloc[-1] == "Bank Transfer")
check("Pattern", "P5 rent index falls with distance", Q["09_rent_index_by_distance"].avg_rent_index.is_monotonic_decreasing)
check("Pattern", "P6 Sydney is the #1 supply-pressure city", Q["08_supply_gap_by_city"].sort_values("pressure_rank").city.iloc[0] == "Sydney")
seas = Q["11_seasonality_index"].sort_values("seasonality_index", ascending=False).month_no.head(3).tolist()
check("Pattern", "P1 top-3 lead months are Jul/Aug/Sep", set(seas) == {7, 8, 9}, f"top3={seas}")
r12 = Q["12_rating_by_distance"].sort_values("distance_band")
check("Pattern", "Ratings fall with distance", r12.avg_rating.is_monotonic_decreasing)

# ------------------------------------------------------------------ report
passed = sum(r[2] for r in results)
lines = ["# Validation report", "", f"**{passed}/{len(results)} checks passed.**", "",
         "| Layer | Check | Result | Detail |", "|---|---|---|---|"]
for layer, name, ok, detail in results:
    lines.append(f"| {layer} | {name} | {'PASS' if ok else '**FAIL**'} | {detail} |")
(ROOT / "docs" / "validation_report.md").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
sys.exit(0 if passed == len(results) else 1)
