# AI mistakes log

The rule on this project: **AI output is a draft until it has been checked against the source data.**
This is the running log of things Claude got wrong while building StayScope, how each was caught, and the fix.
Entries 1-4 are from the original build session. Add your own as you extend the project - an honest, specific
log is worth more than a clean one.

| # | What the AI produced | How it was caught | Fix |
|---|---|---|---|
| 1 | Data generator made payment retries almost always succeed, so Q05 showed **100% retry recovery for every payment method**. | Eyeballing the Q05 output: a perfect 100% across four methods is implausible. Confirmed by counting bookings where all 3 attempts failed (zero). | Retry failure probability raised to 2.5x the first-attempt rate (capped at 50%). Recovery now 95-100%, and a few bookings legitimately cancel after 3 failed attempts. |
| 2 | Occupancy query (Q07) was SQL-correct, but the **data started cold in Jan 2024**, so every city ramped from ~0% occupancy - a fake "growth" story. | Reading the first rows of the output: Bengaluru at 0.4% occupancy in month 1. | Generator now creates history from Jan 2023; the Q07 calendar starts Jan 2024 so it reports steady state. |
| 3 | Monthly GMV (Q01) showed **-74% MoM in Dec 2025**. | Tail of the output. Lead creation stops 30 Nov, so December bookings are incomplete. | Added `is_partial_month` flag in SQL; the Excel report carries the flag and the README says not to read trend off it. |
| 4 | My own **validator** compared Q10's cumulative GMV to the sum of Q01's already-rounded monthly values and failed. | The one failing check out of 39. Measured the gap before touching the tolerance: $1 on $23.7M (36 months x rounding). | Compare against the exact unrounded total from raw `bookings`, not a sum of rounded numbers. |

## Lessons turned into habits
- Read the first and last rows of every result, not just the middle.
- A suspiciously perfect number (100%, 0%, exact ties) is a bug until proven otherwise.
- When a check fails, **measure the discrepancy before changing the check** - decide whether the data, the query or the validator is wrong.
- A formula that evaluates without error (`#REF!`-free recalc) is not a formula that is right: KPIs were cross-checked against raw tables.
