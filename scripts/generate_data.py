"""
Generate a SYNTHETIC student-housing marketplace dataset and load it into SQLite.

Nothing here is real Amber data. The goal is a realistic, relational dataset with
known, documented patterns so that analysis results can be checked against the
ground truth baked in below (see README -> "Planted patterns").

Planted patterns (used later to verify that the SQL actually finds them):
  P1  Demand peaks in Jul-Sep (autumn intake) and Jan (spring intake).
  P2  Faster first response => higher visit & conversion rate.
  P3  'Aggregator' leads cancel more often than other sources.
  P4  Bank Transfer fails more often than Card/UPI.
  P5  Rent falls with distance from campus.
  P6  Sydney has high demand but thin supply (supply-gap city).
  P7  Units cannot be double-booked (overlap guard) -> supply constrains conversion.
"""
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
rng = np.random.default_rng(SEED)

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "stayscope.db"
SCHEMA = ROOT / "sql" / "schema.sql"

SNAPSHOT = pd.Timestamp("2025-12-31")
LEADS_START, LEADS_END = pd.Timestamp("2023-01-01"), pd.Timestamp("2025-11-30")

# city, country, currency, base monthly rent (USD), demand weight, supply weight
CITIES = [
    ("London", "UK", "GBP", 1300, 1.30, 1.20),
    ("Manchester", "UK", "GBP", 800, 0.80, 1.00),
    ("Melbourne", "Australia", "AUD", 1000, 1.00, 1.00),
    ("Sydney", "Australia", "AUD", 1200, 1.40, 0.45),   # P6 supply gap
    ("Toronto", "Canada", "CAD", 1000, 1.10, 1.00),
    ("Dublin", "Ireland", "EUR", 1100, 0.70, 0.70),
    ("New York", "USA", "USD", 1700, 0.90, 0.90),
    ("Delhi", "India", "INR", 250, 1.20, 1.30),
    ("Bengaluru", "India", "INR", 230, 1.00, 1.10),
    ("Pune", "India", "INR", 180, 0.80, 1.00),
]
TYPE_MULT = {"Shared Room": 0.65, "Private Room": 0.85, "Studio": 1.10, "Apartment": 1.35}
SOURCES = ["Organic", "Paid Search", "Social", "Referral", "Aggregator"]
SOURCE_P = [0.30, 0.25, 0.15, 0.10, 0.20]
CANCEL_P = {"Organic": 0.08, "Paid Search": 0.11, "Social": 0.10, "Referral": 0.06, "Aggregator": 0.24}
METHOD_FAIL = {"Card": 0.06, "UPI": 0.04, "Bank Transfer": 0.14, "Wallet": 0.09}
HOME_COUNTRIES = ["India", "China", "Nigeria", "Vietnam", "Brazil", "UAE", "Nepal", "Pakistan", "UK", "USA"]
HOME_P = [0.30, 0.18, 0.08, 0.06, 0.05, 0.05, 0.06, 0.05, 0.09, 0.08]


def build_static():
    cities = pd.DataFrame(
        [(i + 1, c[0], c[1], c[2]) for i, c in enumerate(CITIES)],
        columns=["city_id", "city", "country", "currency"],
    )
    uni_rows, uid = [], 1
    for cid, c in zip(cities.city_id, CITIES):
        for suffix in ("Central University", "Institute of Technology", "Business School"):
            uni_rows.append((uid, cid, f"{c[0]} {suffix}"))
            uid += 1
    universities = pd.DataFrame(uni_rows, columns=["university_id", "city_id", "name"])

    prop_rows, pid = [], 1
    for cid, c in zip(cities.city_id, CITIES):
        n_props = int(round(45 * c[5]))
        unis = universities.loc[universities.city_id == cid, "university_id"].to_numpy()
        for _ in range(n_props):
            ptype = rng.choice(list(TYPE_MULT), p=[0.25, 0.30, 0.25, 0.20])
            dist = round(float(np.clip(rng.gamma(2.2, 1.2), 0.2, 15)), 2)
            listed = pd.Timestamp("2022-06-01") + pd.Timedelta(days=int(rng.integers(0, 200)))
            prop_rows.append((pid, cid, int(rng.choice(unis)), ptype, dist, listed.date().isoformat()))
            pid += 1
    properties = pd.DataFrame(
        prop_rows, columns=["property_id", "city_id", "university_id", "property_type", "distance_km", "listed_date"]
    )

    unit_rows, uidx = [], 1
    base = {i + 1: c[3] for i, c in enumerate(CITIES)}
    for r in properties.itertuples():
        for _ in range(int(rng.integers(2, 9))):
            decay = 1.12 - 0.035 * r.distance_km                    # P5
            rent = base[r.city_id] * TYPE_MULT[r.property_type] * max(decay, 0.7) * rng.normal(1.0, 0.07)
            unit_rows.append((uidx, r.property_id, round(float(rent), 2)))
            uidx += 1
    units = pd.DataFrame(unit_rows, columns=["unit_id", "property_id", "monthly_rent_usd"])
    return cities, universities, properties, units


def month_weight(ts):
    # P1: autumn intake + January intake
    return {1: 1.5, 2: 0.9, 3: 0.7, 4: 0.7, 5: 0.9, 6: 1.3, 7: 2.0, 8: 2.4, 9: 1.8, 10: 0.8, 11: 0.6, 12: 0.7}[ts.month]


def build_leads_and_bookings(cities, properties, units):
    # --- students & leads -------------------------------------------------------------
    n_leads = 21000
    all_days = pd.date_range(LEADS_START, LEADS_END, freq="D")
    day_w = np.array([month_weight(d) for d in all_days], dtype=float)
    day_w /= day_w.sum()
    lead_days = rng.choice(all_days, size=n_leads, p=day_w)
    demand_w = np.array([c[4] for c in CITIES])
    lead_city = rng.choice(cities.city_id, size=n_leads, p=demand_w / demand_w.sum())
    source = rng.choice(SOURCES, size=n_leads, p=SOURCE_P)

    # P2: response time. ~7% never get a response.
    resp = rng.lognormal(mean=2.2, sigma=1.0, size=n_leads)           # median ~9h
    resp = np.round(np.clip(resp, 0.1, 240), 1)
    never = rng.random(n_leads) < 0.07

    p_visit = 0.60 * np.exp(-resp / 60.0)
    p_visit = np.where(never, 0.03, p_visit)
    visited = rng.random(n_leads) < p_visit

    students = pd.DataFrame(
        {
            "student_id": np.arange(1, n_leads + 1),
            "home_country": rng.choice(HOME_COUNTRIES, size=n_leads, p=HOME_P),
            "signup_date": pd.to_datetime(lead_days).strftime("%Y-%m-%d"),
        }
    )

    leads = pd.DataFrame(
        {
            "lead_id": np.arange(1, n_leads + 1),
            "student_id": np.arange(1, n_leads + 1),
            "city_id": lead_city,
            "created_at": pd.to_datetime(lead_days).strftime("%Y-%m-%d"),
            "source": source,
            "first_response_hrs": np.where(never, np.nan, resp),
            "visited": visited.astype(int),
        }
    )

    # --- conversion with supply constraint (P7) ----------------------------------------
    unit_city = units.merge(properties[["property_id", "city_id"]], on="property_id")
    units_by_city = {cid: g["unit_id"].to_numpy() for cid, g in unit_city.groupby("city_id")}
    rent_of = units.set_index("unit_id")["monthly_rent_usd"].to_dict()
    occupied = {u: [] for u in units.unit_id}                          # unit -> list of (start, end)

    p_conv_given_visit = np.where(resp <= 6, 0.42, np.where(resp <= 24, 0.32, 0.20))
    p_conv_given_visit = np.where(never, 0.10, p_conv_given_visit)

    booking_rows, converted = [], np.zeros(n_leads, dtype=int)
    order = np.argsort(lead_days)                                       # process chronologically
    bid = 1
    for i in order:
        if not visited[i] or rng.random() > p_conv_given_visit[i]:
            continue
        created = pd.Timestamp(lead_days[i])
        booked = created + pd.Timedelta(days=int(rng.integers(3, 15)))
        start = booked + pd.Timedelta(days=int(rng.integers(15, 70)))
        months = int(rng.choice([6, 9, 10, 11, 12], p=[0.15, 0.20, 0.30, 0.10, 0.25]))
        end = start + pd.DateOffset(months=months)
        cand = units_by_city[int(lead_city[i])]
        chosen = None
        for u in rng.choice(cand, size=min(40, len(cand)), replace=False):
            if all(end <= s or start >= e for s, e in occupied[int(u)]):
                chosen = int(u)
                break
        if chosen is None or booked > SNAPSHOT:
            continue                                                    # no inventory -> lost lead
        occupied[chosen].append((start, end))
        converted[i] = 1

        src = source[i]
        if rng.random() < CANCEL_P[src]:                               # P3
            status = "Cancelled"
        elif end < SNAPSHOT:
            status = "Completed"
        else:
            status = "Confirmed"
        booking_rows.append(
            (bid, int(leads.lead_id[i]), int(students.student_id[i]), chosen, booked.date().isoformat(),
             start.date().isoformat(), months, round(rent_of[chosen], 2), status)
        )
        bid += 1

    leads["converted"] = converted
    bookings = pd.DataFrame(
        booking_rows,
        columns=["booking_id", "lead_id", "student_id", "unit_id", "booked_at", "start_date",
                 "duration_months", "monthly_rent_usd", "status"],
    )
    return students, leads, bookings


def build_payments_reviews(cities, leads, bookings, properties, units):
    country_of_city = cities.set_index("city_id")["country"].to_dict()
    unit_to_city = units.merge(properties[["property_id", "city_id"]], on="property_id").set_index("unit_id")["city_id"]
    pay_rows, pid = [], 1
    new_status = []
    for b in bookings.itertuples():
        country = country_of_city[int(unit_to_city[b.unit_id])]
        methods = ["Card", "Bank Transfer", "Wallet"] + (["UPI"] if country == "India" else [])
        probs = [0.50, 0.25, 0.25] if country != "India" else [0.30, 0.15, 0.15, 0.40]
        method = rng.choice(methods, p=probs)
        amount = round(b.monthly_rent_usd * 2, 2)                       # first month + 1-month deposit
        paid_at = pd.Timestamp(b.booked_at)
        ok = False
        for attempt in range(1, 4):
            fail = rng.random() < min(0.5, METHOD_FAIL[method] * (1.0 if attempt == 1 else 2.5))   # P4; retries are less reliable
            pay_rows.append((pid, b.booking_id, attempt, method, amount,
                             "Failed" if fail else "Success", (paid_at + pd.Timedelta(days=attempt - 1)).date().isoformat()))
            pid += 1
            if not fail:
                ok = True
                break
            method = rng.choice(["Card", "Wallet"])                     # students retry with another method
        new_status.append(b.status if ok else "Cancelled")
    bookings = bookings.copy()
    bookings["status"] = new_status
    payments = pd.DataFrame(
        pay_rows, columns=["payment_id", "booking_id", "attempt_no", "method", "amount_usd", "status", "paid_at"]
    )

    # reviews only for Completed bookings, ~45% leave one; rating falls with distance
    dist = (units.merge(properties[["property_id", "distance_km"]], on="property_id")
            .set_index("unit_id")["distance_km"])
    rev_rows, rid = [], 1
    for b in bookings[bookings.status == "Completed"].itertuples():
        if rng.random() > 0.45:
            continue
        mu = 4.4 - 0.10 * dist[b.unit_id]
        rating = int(np.clip(np.round(rng.normal(mu, 0.8)), 1, 5))
        end = pd.Timestamp(b.start_date) + pd.DateOffset(months=b.duration_months)
        rev_rows.append((rid, b.booking_id, rating, end.date().isoformat()))
        rid += 1
    reviews = pd.DataFrame(rev_rows, columns=["review_id", "booking_id", "rating", "created_at"])
    return bookings, payments, reviews


def main():
    cities, universities, properties, units = build_static()
    students, leads, bookings = build_leads_and_bookings(cities, properties, units)
    bookings, payments, reviews = build_payments_reviews(cities, leads, bookings, properties, units)

    DB_PATH.parent.mkdir(exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()
    con = sqlite3.connect(DB_PATH)
    con.executescript(SCHEMA.read_text())
    for name, df in [("cities", cities), ("universities", universities), ("properties", properties),
                     ("units", units), ("students", students), ("leads", leads),
                     ("bookings", bookings), ("payments", payments), ("reviews", reviews)]:
        df.to_sql(name, con, if_exists="append", index=False)
        print(f"{name:13s} {len(df):>7,d} rows")
    con.commit()
    con.close()
    print(f"\nDatabase written to {DB_PATH}")


if __name__ == "__main__":
    main()
