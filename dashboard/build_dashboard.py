"""Inject aggregated data from the SQLite DB into template.html -> self-contained interactive dashboard."""
import json, sqlite3
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
con = sqlite3.connect(ROOT / "data" / "stayscope.db")
CUT = "2025-11"  # Dec 2025 is partial -> excluded everywhere
q = lambda s: pd.read_sql_query(s, con)

lc = q(f"""SELECT c.city, strftime('%Y-%m', l.created_at) m, COUNT(*) leads, SUM(l.visited) visits, SUM(l.converted) conv
           FROM leads l JOIN cities c USING(city_id) WHERE m <= '{CUT}' GROUP BY 1,2""")
bk = q(f"""SELECT c.city, strftime('%Y-%m', b.booked_at) m,
           SUM(b.status IN ('Confirmed','Completed')) ret,
           ROUND(SUM(CASE WHEN b.status IN ('Confirmed','Completed') THEN b.monthly_rent_usd*b.duration_months ELSE 0 END)) gmv,
           SUM(b.status='Cancelled') canc
           FROM bookings b JOIN units u USING(unit_id) JOIN properties p USING(property_id) JOIN cities c ON c.city_id=p.city_id
           WHERE m <= '{CUT}' GROUP BY 1,2""")
occ = pd.read_csv(ROOT / "exports" / "07_occupancy_by_city_month.csv").rename(columns={"occupied_units": "occ_n"})
cm = lc.merge(bk, on=["city", "m"], how="outer").fillna(0).merge(occ[["city", "month", "occ_n", "total_units"]],
        left_on=["city", "m"], right_on=["city", "month"], how="left")
cm = cm[cm.m <= CUT]
rows = [[r.city, r.m, int(r.leads), int(r.visits), int(r.conv), int(r.ret), float(r.gmv), int(r.canc),
         None if pd.isna(r.occ_n) else int(r.occ_n), None if pd.isna(r.total_units) else int(r.total_units)]
        for r in cm.itertuples()]

cs = q(f"""SELECT c.city, CAST(strftime('%Y', b.booked_at) AS INT) y, l.source, COUNT(*) n, SUM(b.status='Cancelled') x
           FROM bookings b JOIN leads l USING(lead_id) JOIN units u USING(unit_id) JOIN properties p USING(property_id)
           JOIN cities c ON c.city_id=p.city_id WHERE strftime('%Y-%m', b.booked_at) <= '{CUT}' GROUP BY 1,2,3""")
cr = q(f"""SELECT c.city, CAST(strftime('%Y', l.created_at) AS INT) y,
           CASE WHEN first_response_hrs IS NULL THEN 'No reply' WHEN first_response_hrs<=1 THEN '≤ 1h'
                WHEN first_response_hrs<=6 THEN '1–6h' WHEN first_response_hrs<=24 THEN '6–24h' ELSE '> 24h' END b,
           COUNT(*) n, SUM(visited) v, SUM(converted) k
           FROM leads l JOIN cities c USING(city_id) WHERE strftime('%Y-%m', l.created_at) <= '{CUT}' GROUP BY 1,2,3""")
cp = q(f"""SELECT c.city, CAST(strftime('%Y', b.booked_at) AS INT) y, pay.method, COUNT(*) n, SUM(pay.status='Failed') f
           FROM payments pay JOIN bookings b USING(booking_id) JOIN units u USING(unit_id) JOIN properties p USING(property_id)
           JOIN cities c ON c.city_id=p.city_id WHERE pay.attempt_no=1 AND strftime('%Y-%m', b.booked_at) <= '{CUT}' GROUP BY 1,2,3""")
units = q("SELECT c.city, COUNT(*) n FROM units u JOIN properties p USING(property_id) JOIN cities c USING(city_id) GROUP BY 1")
data = {"cities": sorted(units.city), "units": dict(zip(units.city, map(int, units.n))), "cm": rows,
        "cs": cs.values.tolist(), "cr": cr.values.tolist(), "cp": cp.values.tolist()}
html = (ROOT / "dashboard" / "template.html").read_text(encoding="utf-8").replace("__DATA__", json.dumps(data, ensure_ascii=False, separators=(",", ":")))
out = ROOT / "dashboard" / "stayscope_dashboard.html"
out.write_text(html, encoding="utf-8")
(ROOT / "docs" / "index.html").write_text(html, encoding="utf-8")   # served by GitHub Pages
print(f"built {out} ({len(html)/1024:.0f} KB), city-month rows: {len(rows)}")
