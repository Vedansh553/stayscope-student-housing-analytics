-- Q04: Cancellation rate by lead source
-- Business question: Which acquisition channels bring bookings that stick?
-- Note: includes cancellations caused by exhausted payment retries.
SELECT l.source,
       COUNT(*)                                                   AS bookings,
       SUM(CASE WHEN b.status = 'Cancelled' THEN 1 ELSE 0 END)    AS cancelled,
       ROUND(100.0 * AVG(CASE WHEN b.status = 'Cancelled' THEN 1.0 ELSE 0 END), 1) AS cancel_rate_pct,
       ROUND(SUM(CASE WHEN b.status <> 'Cancelled'
                      THEN b.monthly_rent_usd * b.duration_months ELSE 0 END), 0)   AS retained_gmv_usd
FROM bookings b
JOIN leads l ON l.lead_id = b.lead_id
GROUP BY l.source
ORDER BY cancel_rate_pct DESC;
