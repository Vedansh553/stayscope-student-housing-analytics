-- Q10: Cumulative GMV and 3-month rolling average bookings
-- Business question: What is the run-rate, smoothed for seasonality?
WITH monthly AS (
    SELECT strftime('%Y-%m', booked_at) AS month,
           COUNT(*)                     AS bookings,
           SUM(monthly_rent_usd * duration_months) AS gmv_usd
    FROM bookings
    WHERE status IN ('Confirmed', 'Completed')
    GROUP BY 1
)
SELECT month,
       bookings,
       ROUND(gmv_usd, 0)                                                     AS gmv_usd,
       ROUND(SUM(gmv_usd) OVER (ORDER BY month), 0)                          AS cumulative_gmv_usd,
       ROUND(AVG(bookings) OVER (ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 1) AS rolling_3m_avg_bookings
FROM monthly
ORDER BY month;
