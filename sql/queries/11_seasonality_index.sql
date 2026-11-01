-- Q11: Lead seasonality index by calendar month (2024-2025 combined)
-- Business question: When should marketing spend and support staffing peak?
-- Index 100 = an average month; computed with a window average over the 12 months.
WITH by_month AS (
    SELECT CAST(strftime('%m', created_at) AS INTEGER) AS month_no,
           COUNT(*) AS leads
    FROM leads
    GROUP BY 1
)
SELECT month_no,
       leads,
       ROUND(100.0 * leads / AVG(leads) OVER (), 0) AS seasonality_index
FROM by_month
ORDER BY month_no;
