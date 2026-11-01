-- Q05: Payment first-attempt failure rate and retry recovery, by method
-- Business question: Which payment methods leak revenue, and do retries recover it?
WITH first_try AS (
    SELECT booking_id, method, status
    FROM payments
    WHERE attempt_no = 1
),
recovered AS (
    SELECT DISTINCT p.booking_id
    FROM payments p
    WHERE p.status = 'Success' AND p.attempt_no > 1
)
SELECT f.method,
       COUNT(*)                                                      AS first_attempts,
       SUM(CASE WHEN f.status = 'Failed' THEN 1 ELSE 0 END)          AS first_try_failures,
       ROUND(100.0 * AVG(CASE WHEN f.status = 'Failed' THEN 1.0 ELSE 0 END), 1) AS first_try_fail_pct,
       SUM(CASE WHEN f.status = 'Failed' AND r.booking_id IS NOT NULL THEN 1 ELSE 0 END) AS recovered_on_retry,
       ROUND(100.0 * SUM(CASE WHEN f.status = 'Failed' AND r.booking_id IS NOT NULL THEN 1 ELSE 0 END)
             / NULLIF(SUM(CASE WHEN f.status = 'Failed' THEN 1 ELSE 0 END), 0), 1) AS retry_recovery_pct
FROM first_try f
LEFT JOIN recovered r ON r.booking_id = f.booking_id
GROUP BY f.method
ORDER BY first_try_fail_pct DESC;
