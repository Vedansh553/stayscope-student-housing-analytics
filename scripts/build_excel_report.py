"""
Rebuild the stakeholder Excel report from the database in one command.

Design rules (so the workbook stays trustworthy when someone edits it):
  * Raw query results are pasted as VALUES on data sheets (blue = hardcoded from SQL).
  * Every rate, total and KPI is an Excel FORMULA that points at those cells (black).
  * Assumptions/definitions are written next to the numbers they affect.
"""
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "exports"
OUT = ROOT / "StayScope_Report.xlsx"

F = "Arial"
HEAD = PatternFill("solid", fgColor="1F3A5F")
f_head = Font(name=F, bold=True, color="FFFFFF", size=10)
f_in = Font(name=F, color="0000FF", size=10)       # hardcoded input from SQL
f_calc = Font(name=F, color="000000", size=10)     # formula
f_title = Font(name=F, bold=True, size=14, color="1F3A5F")
f_note = Font(name=F, italic=True, size=9, color="555555")

wb = Workbook()


def write_table(ws, df, start_row=4, input_cols=None, widths=None):
    """Write df as a table; columns in input_cols are blue hardcoded values."""
    for j, col in enumerate(df.columns, 1):
        c = ws.cell(row=start_row, column=j, value=col)
        c.font, c.fill = f_head, HEAD
        c.alignment = Alignment(horizontal="center", wrap_text=True)
    for i, row in enumerate(df.itertuples(index=False), start_row + 1):
        for j, v in enumerate(row, 1):
            c = ws.cell(row=i, column=j, value=None if pd.isna(v) else v)
            c.font = f_in
    for j in range(1, len(df.columns) + 1):
        ws.column_dimensions[get_column_letter(j)].width = (widths or {}).get(j, 16)
    ws.freeze_panes = ws.cell(row=start_row + 1, column=1)


def title(ws, text, note):
    ws["A1"] = text
    ws["A1"].font = f_title
    ws["A2"] = note
    ws["A2"].font = f_note


# ------------------------------------------------------------------ Monthly GMV
m = pd.read_csv(EXP / "01_monthly_gmv_mom.csv")[["month", "bookings", "gmv_usd", "is_partial_month"]]
ws_m = wb.active
ws_m.title = "Monthly GMV"
title(ws_m, "Monthly GMV & bookings",
      "GMV = monthly rent x duration for Confirmed+Completed bookings, by booking month. "
      "Months flagged partial (col E) have incomplete data - exclude from trend reading.")
write_table(ws_m, m.assign(mom_growth_pct=None), 4)
ws_m["D4"], ws_m["E4"] = "is_partial_month", "MoM growth %"
ws_m["D4"].font = ws_m["E4"].font = f_head
ws_m["E4"].fill = HEAD
first, last = 5, 4 + len(m)
for r in range(first, last + 1):
    ws_m.cell(row=r, column=5).value = None if r == first else f'=IF(C{r-1}=0,"",(C{r}-C{r-1})/C{r-1})'
    ws_m.cell(row=r, column=5).number_format = "0.0%"
    ws_m.cell(row=r, column=5).font = f_calc
    ws_m.cell(row=r, column=3).number_format = "$#,##0"
for r in range(first, last + 1):
    ws_m.cell(row=r, column=2).number_format = "#,##0"
ch = LineChart()
ch.title, ch.height, ch.width = "Monthly GMV (USD)", 8, 18
ch.add_data(Reference(ws_m, min_col=3, min_row=4, max_row=last), titles_from_data=True)
ch.set_categories(Reference(ws_m, min_col=1, min_row=first, max_row=last))
ws_m.add_chart(ch, "G4")

# ------------------------------------------------------------------ Funnel
fu = pd.read_csv(EXP / "02_funnel_by_city.csv")[["city", "country", "leads", "visits", "bookings"]]
ws_f = wb.create_sheet("Funnel by City")
title(ws_f, "Lead -> visit -> booking funnel by city", "Counts are SQL outputs (blue). Rates are live formulas (black).")
write_table(ws_f, fu.assign(lead_to_visit=None, visit_to_booking=None, lead_to_booking=None), 4)
for j, h in enumerate(["Lead->visit %", "Visit->booking %", "Lead->booking %"], 6):
    c = ws_f.cell(row=4, column=j, value=h)
    c.font, c.fill, c.alignment = f_head, HEAD, Alignment(horizontal="center", wrap_text=True)
f_first, f_last = 5, 4 + len(fu)
for r in range(f_first, f_last + 1):
    for col, expr in [(6, f"=D{r}/C{r}"), (7, f"=E{r}/D{r}"), (8, f"=E{r}/C{r}")]:
        c = ws_f.cell(row=r, column=col, value=expr)
        c.font, c.number_format = f_calc, "0.0%"
tr = f_last + 1
ws_f.cell(row=tr, column=1, value="Total").font = Font(name=F, bold=True)
for col in (3, 4, 5):
    L = get_column_letter(col)
    c = ws_f.cell(row=tr, column=col, value=f"=SUM({L}{f_first}:{L}{f_last})")
    c.font = Font(name=F, bold=True)
for col, expr in [(6, f"=D{tr}/C{tr}"), (7, f"=E{tr}/D{tr}"), (8, f"=E{tr}/C{tr}")]:
    c = ws_f.cell(row=tr, column=col, value=expr)
    c.font, c.number_format = Font(name=F, bold=True), "0.0%"
bc = BarChart()
bc.title, bc.height, bc.width = "Lead -> booking conversion by city", 8, 18
bc.add_data(Reference(ws_f, min_col=8, min_row=4, max_row=f_last), titles_from_data=True)
bc.set_categories(Reference(ws_f, min_col=1, min_row=f_first, max_row=f_last))
bc.y_axis.number_format = "0%"
ws_f.add_chart(bc, "J4")

# ------------------------------------------------------------------ Response time
rt = pd.read_csv(EXP / "03_response_time_vs_conversion.csv")[["response_bucket", "leads"]]
raw = pd.read_csv(ROOT / "exports" / "03_response_time_vs_conversion.csv")
rt["visited"] = (raw.leads * raw.visit_rate_pct / 100).round().astype(int)
rt["booked"] = (raw.leads * raw.booking_rate_pct / 100).round().astype(int)
ws_r = wb.create_sheet("Response Time")
title(ws_r, "Does reply speed change conversion?",
      "visited/booked counts are back-computed from SQL rates (rounded); rates below are formulas.")
write_table(ws_r, rt.assign(visit_rate=None, booking_rate=None), 4, widths={1: 18})
for j, h in enumerate(["Visit rate", "Booking rate"], 5):
    c = ws_r.cell(row=4, column=j, value=h)
    c.font, c.fill = f_head, HEAD
for r in range(5, 5 + len(rt)):
    for col, expr in [(5, f"=C{r}/B{r}"), (6, f"=D{r}/B{r}")]:
        c = ws_r.cell(row=r, column=col, value=expr)
        c.font, c.number_format = f_calc, "0.0%"
bc2 = BarChart()
bc2.title, bc2.height, bc2.width = "Booking rate by first-response time", 8, 16
bc2.add_data(Reference(ws_r, min_col=6, min_row=4, max_row=4 + len(rt)), titles_from_data=True)
bc2.set_categories(Reference(ws_r, min_col=1, min_row=5, max_row=4 + len(rt)))
bc2.y_axis.number_format = "0%"
ws_r.add_chart(bc2, "H4")

# ------------------------------------------------------------------ Supply gap
sg = pd.read_csv(EXP / "08_supply_gap_by_city.csv")[["city", "units", "leads_2025"]]
ws_s = wb.create_sheet("Supply Gap")
title(ws_s, "Demand vs supply by city (2025)", "Leads per unit = leads_2025 / units. Higher = tighter supply.")
write_table(ws_s, sg.assign(leads_per_unit=None, vs_median=None), 4)
for j, h in enumerate(["Leads per unit", "x vs median city"], 4):
    c = ws_s.cell(row=4, column=j, value=h)
    c.font, c.fill = f_head, HEAD
s_first, s_last = 5, 4 + len(sg)
for r in range(s_first, s_last + 1):
    c = ws_s.cell(row=r, column=4, value=f"=C{r}/B{r}")
    c.font, c.number_format = f_calc, "0.00"
    c = ws_s.cell(row=r, column=5, value=f"=D{r}/MEDIAN($D${s_first}:$D${s_last})")
    c.font, c.number_format = f_calc, '0.0"x"'
bc3 = BarChart()
bc3.title, bc3.height, bc3.width = "Leads per available unit (2025)", 8, 16
bc3.add_data(Reference(ws_s, min_col=4, min_row=4, max_row=s_last), titles_from_data=True)
bc3.set_categories(Reference(ws_s, min_col=1, min_row=s_first, max_row=s_last))
ws_s.add_chart(bc3, "G4")

# ------------------------------------------------------------------ Cancellations & payments
cn = pd.read_csv(EXP / "04_cancellation_by_source.csv")[["source", "bookings", "cancelled"]]
ws_c = wb.create_sheet("Cancellations")
title(ws_c, "Cancellation rate by lead source", "Includes cancellations from exhausted payment retries.")
write_table(ws_c, cn.assign(cancel_rate=None), 4)
ws_c.cell(row=4, column=4, value="Cancel rate").font = f_head
ws_c.cell(row=4, column=4).fill = HEAD
for r in range(5, 5 + len(cn)):
    c = ws_c.cell(row=r, column=4, value=f"=C{r}/B{r}")
    c.font, c.number_format = f_calc, "0.0%"

py = pd.read_csv(EXP / "05_payment_failure_by_method.csv")[["method", "first_attempts", "first_try_failures", "recovered_on_retry"]]
ws_p = wb.create_sheet("Payments")
title(ws_p, "First-attempt payment failure & retry recovery", "Recovery = failed first try that later succeeded.")
write_table(ws_p, py.assign(fail_rate=None, recovery_rate=None), 4)
for j, h in enumerate(["First-try fail rate", "Retry recovery rate"], 5):
    c = ws_p.cell(row=4, column=j, value=h)
    c.font, c.fill = f_head, HEAD
for r in range(5, 5 + len(py)):
    for col, expr in [(5, f"=C{r}/B{r}"), (6, f"=IF(C{r}=0,0,D{r}/C{r})")]:
        c = ws_p.cell(row=r, column=col, value=expr)
        c.font, c.number_format = f_calc, "0.0%"
ws_p.column_dimensions["E"].width = ws_p.column_dimensions["F"].width = 20

# ------------------------------------------------------------------ KPI summary (first sheet)
ws_k = wb.create_sheet("KPI Summary", 0)
title(ws_k, "StayScope - KPI summary (SYNTHETIC data)", "Every number on this page is a formula pointing at the data sheets.")
ws_k.column_dimensions["A"].width = 38
ws_k.column_dimensions["B"].width = 20
ws_k.column_dimensions["C"].width = 70
kpis = [
    ("Total GMV (USD)", f"=SUM('Monthly GMV'!C{first}:C{last})", "$#,##0", "Confirmed + Completed bookings, all months"),
    ("Total bookings (retained)", f"=SUM('Monthly GMV'!B{first}:B{last})", "#,##0", "Excludes Cancelled"),
    ("Average booking value (USD)", "=B5/B6", "$#,##0", "GMV / retained bookings"),
    ("Total leads", f"='Funnel by City'!C{tr}", "#,##0", ""),
    ("Lead -> booking conversion", f"='Funnel by City'!H{tr}", "0.0%", "Booked (incl. later cancelled) / leads"),
    ("Visit -> booking conversion", f"='Funnel by City'!G{tr}", "0.0%", ""),
    ("Highest cancel rate (source)", f"=INDEX(Cancellations!A5:A{4+len(cn)},MATCH(MAX(Cancellations!D5:D{4+len(cn)}),Cancellations!D5:D{4+len(cn)},0))", "@", "Acquisition channel with worst retention"),
    ("   ...its cancel rate", f"=MAX(Cancellations!D5:D{4+len(cn)})", "0.0%", ""),
    ("Tightest-supply city", f"=INDEX('Supply Gap'!A{s_first}:A{s_last},MATCH(MAX('Supply Gap'!D{s_first}:D{s_last}),'Supply Gap'!D{s_first}:D{s_last},0))", "@", "Most leads per available unit, 2025"),
    ("   ...leads per unit", f"=MAX('Supply Gap'!D{s_first}:D{s_last})", "0.0", ""),
    ("Worst payment method (first try)", f"=INDEX(Payments!A5:A{4+len(py)},MATCH(MAX(Payments!E5:E{4+len(py)}),Payments!E5:E{4+len(py)},0))", "@", ""),
    ("   ...first-try failure rate", f"=MAX(Payments!E5:E{4+len(py)})", "0.0%", ""),
]
for j, h in enumerate(["Metric", "Value", "Definition / note"], 1):
    c = ws_k.cell(row=4, column=j, value=h)
    c.font, c.fill = f_head, HEAD
for i, (name, formula, fmt, note) in enumerate(kpis, 5):
    ws_k.cell(row=i, column=1, value=name).font = f_calc
    c = ws_k.cell(row=i, column=2, value=formula)
    c.font, c.number_format = Font(name=F, bold=True, size=10), fmt
    c.alignment = Alignment(horizontal="right")
    ws_k.cell(row=i, column=3, value=note).font = f_note
ws_k.cell(row=5 + len(kpis) + 1, column=1,
          value="Colour code: blue = value pasted from SQL, black = formula. Synthetic data - no real company figures.").font = f_note

wb.save(OUT)
print("saved", OUT)
