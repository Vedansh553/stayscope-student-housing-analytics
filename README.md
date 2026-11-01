# StayScope - Student Housing Marketplace Analytics

An end-to-end analytics project for a **student accommodation marketplace** (leads -> visits -> bookings -> payments -> reviews):
a relational SQL database, 12 analytical queries, an automated validation harness, a formula-driven Excel report and a
Power BI / Tableau build guide. Built AI-first, with every number re-derived before it is trusted.

> **All data is synthetic** (seeded generator, `scripts/generate_data.py`). No real company data is used. The generator
> plants known patterns, and the validation harness checks that the SQL analysis recovers them.

## Quick start
```bash
pip install -r requirements.txt
./run_all.sh          # generate data -> run 12 queries -> validate (39 checks) -> build Excel report
```

## What's inside
| Path | What it is |
|---|---|
| `sql/schema.sql` | 9-table schema with PK/FK/CHECK constraints and indexes |
| `sql/queries/` | 12 queries: joins, aggregations, **window functions** (LAG, RANK, ROW_NUMBER, rolling AVG, running SUM), CTEs, a recursive calendar |
| `scripts/validate.py` | 39 checks: data quality, **SQL vs pandas reconciliation**, pattern recovery |
| `scripts/build_excel_report.py` | Rebuilds `StayScope_Report.xlsx` (126 formulas, 5 charts, KPI sheet) |
| `exports/` | Query results as CSV, ready for Power BI / Tableau |
| `docs/` | Validation report, **AI mistakes log**, AI workflow and prompts, dashboard guide |

## Interactive dashboard
**Live demo:** https://vedansh553.github.io/stayscope-student-housing-analytics/  (city/year filters, click a bar to drill in)

Source: `dashboard/template.html` + `dashboard/build_dashboard.py` (injects aggregates from the SQLite DB; `docs/index.html` is the built page served by GitHub Pages).
Rebuild after regenerating data: `python dashboard/build_dashboard.py`.

## Findings (from the synthetic data)
1. **Reply speed is the biggest conversion lever.** Booking rate: 27.0% (<=1h), 22.9% (1-6h), 14.8% (6-24h), 5.8% (>24h), 0.3% (never answered). Leads waiting >24h or unanswered are ~22% of volume.
2. **Sydney is supply-constrained.** 8.7 leads per unit vs ~3 in other cities; visit-to-booking is 25.8% vs 33-36% elsewhere; 2025 occupancy ~82% vs 32-42% for other cities. Add inventory there first.
3. **Aggregator bookings churn.** 25.6% cancel vs 6.4% for Referral and 8.3% for Organic.
4. **Bank Transfer leaks revenue.** 16.2% first-try failure vs 3.9% (UPI) and 5.9% (Card); retries recover most of it, but not all.
5. **Demand is sharply seasonal.** July-September leads run at 150-208% of an average month; Nov-Dec at 40-53%.
6. **Proximity carries a premium and better ratings.** Units under 1 km rent at ~1.07x city average vs 0.93x at 4-7 km; average rating is 4.19 under 2 km vs 3.85 beyond 5 km.

## Definitions & caveats
- **GMV** = monthly rent x duration, Confirmed + Completed bookings, by booking month.
- Dec 2025 is a **partial month** (leads stop 30 Nov); flagged in Q01 and the Excel report.
- Findings 2-6 are patterns the generator plants, so they show the *method works*, not what is true of any real market.
- Occupancy treats all units as available for the whole window.

## AI usage
Built with Claude (chat) for the schema, generator, queries, validation harness and report script. Prompts and checks:
`docs/ai_workflow.md`. What the AI got wrong and how it was caught: `docs/ai_mistakes_log.md`.
