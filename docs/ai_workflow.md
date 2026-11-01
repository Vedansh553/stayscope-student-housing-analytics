# AI-assisted workflow & reusable prompts

How AI tools were used, and the prompt patterns worth reusing. Everything AI produced went through
`scripts/validate.py` before being trusted.

## Where AI helped
| Task | Tool | Human check |
|---|---|---|
| Schema design, synthetic data generator with *documented* planted patterns | Claude (chat) | Planted patterns are asserted in `validate.py` (layer 3) |
| Drafting 12 SQL queries (joins, CTEs, window functions, recursive calendar) | Claude (chat) | Independent pandas recomputation (layer 2) |
| Validation harness and Excel report script | Claude (chat) | Cross-check of KPI cells vs raw tables |
| README / docs | Claude (chat) | Numbers copied from exported CSVs, not typed from memory |

## Prompt patterns

**1. SQL drafting - give schema, grain and definitions up front**
> Here is my schema (paste `schema.sql`). Write a SQLite query for [business question].
> Grain: one row per [city-month]. Definitions: GMV = monthly_rent x duration_months for status IN (Confirmed, Completed).
> Use a CTE per logical step and comment every assumption. Do not use functions unsupported by SQLite.

**2. Make the AI try to break its own query**
> List 5 ways this query could return a wrong number without raising an error (duplicate join rows, NULL handling,
> partial periods, double counting, filter placed in WHERE vs ON). For each, give a SQL check I can run.

**3. Reconciliation request**
> Give me a pandas snippet that recomputes the headline numbers of this query from the raw tables, without using the
> same logic, so I can diff the two results.

**4. Interpretation guard**
> Here is the output table. Write 3 observations. For each, say what sample size it rests on and one reason it might
> be an artifact (cold start, partial period, small n) rather than a real effect.

## Automations in this repo
- `run_all.sh` - regenerate data, run all queries, validate, rebuild the Excel report in one command.
- `scripts/build_excel_report.py` - rebuilds the formula-driven stakeholder workbook from the database.
- `exports/*.csv` - query outputs ready to load into Power BI / Tableau.
