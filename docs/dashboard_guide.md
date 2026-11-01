# Power BI / Tableau build guide

The `.pbix` / `.twbx` file itself is **not** in this repo - build it from `exports/*.csv` (about 1-2 hours), add a
screenshot to the README, and link the published/Loom walkthrough.

## Data model (Power BI)
Load: `01_monthly_gmv_mom`, `02_funnel_by_city`, `03_response_time_vs_conversion`, `04_cancellation_by_source`,
`05_payment_failure_by_method`, `07_occupancy_by_city_month`, `08_supply_gap_by_city`, `11_seasonality_index`.
Relate the city-level tables on `city`.

## DAX measures
```DAX
Total GMV = SUM('01_monthly_gmv_mom'[gmv_usd])
Retained Bookings = SUM('01_monthly_gmv_mom'[bookings])
Avg Booking Value = DIVIDE([Total GMV], [Retained Bookings])
Lead to Booking % = DIVIDE(SUM('02_funnel_by_city'[bookings]), SUM('02_funnel_by_city'[leads]))
Visit to Booking % = DIVIDE(SUM('02_funnel_by_city'[bookings]), SUM('02_funnel_by_city'[visits]))
Leads per Unit = DIVIDE(SUM('08_supply_gap_by_city'[leads_2025]), SUM('08_supply_gap_by_city'[units]))
Cancel Rate % = DIVIDE(SUM('04_cancellation_by_source'[cancelled]), SUM('04_cancellation_by_source'[bookings]))
```

## Pages
1. **Executive overview** - KPI cards (GMV, bookings, conversion), monthly GMV line (hide months where `is_partial_month = 1`).
2. **Funnel & response time** - funnel by city, booking rate by response bucket.
3. **Supply & occupancy** - leads-per-unit bar, occupancy heat-map (city x month).
4. **Retention & payments** - cancel rate by source, first-try failure by payment method.

Slicers: city, country, year. Add a text box on every page: "Synthetic data. See docs/validation_report.md."
