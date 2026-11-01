-- Q03: Does first-response speed change visit and booking rates?
-- Business question: What is the value of replying faster?
-- NULL first_response_hrs = the lead was never answered; kept as its own bucket.
WITH bucketed AS (
    SELECT CASE
             WHEN first_response_hrs IS NULL THEN '5. No response'
             WHEN first_response_hrs <= 1   THEN '1. <= 1h'
             WHEN first_response_hrs <= 6   THEN '2. 1-6h'
             WHEN first_response_hrs <= 24  THEN '3. 6-24h'
             ELSE '4. > 24h'
           END AS response_bucket,
           visited, converted
    FROM leads
)
SELECT response_bucket,
       COUNT(*)                                       AS leads,
       ROUND(100.0 * AVG(visited), 1)                 AS visit_rate_pct,
       ROUND(100.0 * AVG(converted), 1)               AS booking_rate_pct,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS share_of_leads_pct
FROM bucketed
GROUP BY response_bucket
ORDER BY response_bucket;
