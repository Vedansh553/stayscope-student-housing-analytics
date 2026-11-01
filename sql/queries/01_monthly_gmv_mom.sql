-- Q01: Monthly GMV, bookings and month-over-month growth
-- Business question: Is the marketplace growing, and how seasonal is it?
-- Definition: GMV = monthly_rent * duration_months for Confirmed + Completed bookings,
--             attributed to the month the booking was made. Cancelled bookings are excluded.
WITH monthly AS (
    SELECT strftime('%Y-%m', booked_at)              AS month,
           COUNT(*)                                  AS bookings,
           ROUND(SUM(monthly_rent_usd * duration_months), 0) AS gmv_usd
    FROM bookings
    WHERE status IN ('Confirmed', 'Completed')
    GROUP BY 1
)
SELECT month,
       bookings,
       gmv_usd,
       LAG(gmv_usd) OVER (ORDER BY month)            AS prev_month_gmv,
       ROUND(100.0 * (gmv_usd - LAG(gmv_usd) OVER (ORDER BY month))
             / NULLIF(LAG(gmv_usd) OVER (ORDER BY month), 0), 1) AS mom_growth_pct,
       -- Leads stop at the cut-off date, so bookings in later months are incomplete: flag, don't trust.
       CASE WHEN month > (SELECT strftime('%Y-%m', MAX(created_at)) FROM leads)
            THEN 1 ELSE 0 END                         AS is_partial_month
FROM monthly
ORDER BY month;
