# Validation report

**39/39 checks passed.**

| Layer | Check | Result | Detail |
|---|---|---|---|
| Data quality | cities.city_id unique & non-null | PASS |  |
| Data quality | properties.property_id unique & non-null | PASS |  |
| Data quality | units.unit_id unique & non-null | PASS |  |
| Data quality | leads.lead_id unique & non-null | PASS |  |
| Data quality | bookings.booking_id unique & non-null | PASS |  |
| Data quality | payments.payment_id unique & non-null | PASS |  |
| Data quality | reviews.review_id unique & non-null | PASS |  |
| Data quality | No orphan properties.city_id -> cities | PASS | 0 orphans |
| Data quality | No orphan units.property_id -> properties | PASS | 0 orphans |
| Data quality | No orphan leads.city_id -> cities | PASS | 0 orphans |
| Data quality | No orphan bookings.lead_id -> leads | PASS | 0 orphans |
| Data quality | No orphan bookings.unit_id -> units | PASS | 0 orphans |
| Data quality | No orphan payments.booking_id -> bookings | PASS | 0 orphans |
| Data quality | No orphan reviews.booking_id -> bookings | PASS | 0 orphans |
| Data quality | booked_at >= lead created_at | PASS |  |
| Data quality | start_date after booked_at | PASS |  |
| Data quality | No double-booked units | PASS | 0 overlaps |
| Data quality | leads.converted == presence of a booking | PASS |  |
| Data quality | booking rent == unit rent (snapshot) | PASS |  |
| Data quality | <= 1 successful payment per booking | PASS |  |
| Data quality | Reviews only on Completed bookings | PASS |  |
| Reconciliation | Q01 monthly bookings match pandas | PASS |  |
| Reconciliation | Q01 monthly GMV matches pandas (±$1 rounding) | PASS |  |
| Reconciliation | Q01 total GMV == pandas total | PASS |  |
| Reconciliation | Q10 final cumulative GMV == exact raw total (±$1) | PASS |  |
| Reconciliation | Q02 leads sum == leads table rows | PASS |  |
| Reconciliation | Q02 bookings sum == bookings table rows | PASS |  |
| Reconciliation | Q02 visits sum == SUM(leads.visited) | PASS |  |
| Reconciliation | Q03 buckets cover every lead exactly once | PASS |  |
| Reconciliation | Q04 cancel rate matches pandas | PASS |  |
| Reconciliation | Q05 first attempts == number of bookings | PASS |  |
| Reconciliation | Q07 occupied units match pandas (8 random city-months) | PASS | 0 mismatches |
| Pattern | P2 booking rate falls as response time rises | PASS |  |
| Pattern | P3 Aggregator has the highest cancellation rate | PASS |  |
| Pattern | P4 Bank Transfer has the highest first-try failure | PASS |  |
| Pattern | P5 rent index falls with distance | PASS |  |
| Pattern | P6 Sydney is the #1 supply-pressure city | PASS |  |
| Pattern | P1 top-3 lead months are Jul/Aug/Sep | PASS | top3=[8, 7, 9] |
| Pattern | Ratings fall with distance | PASS |  |
