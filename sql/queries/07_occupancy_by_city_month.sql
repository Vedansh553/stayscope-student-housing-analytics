-- Q07: Occupancy rate by city and month (units under an active booking / total units)
-- Business question: How full is each city's inventory through the year?
-- Assumptions: all units are treated as available throughout; Cancelled bookings do not occupy.
-- Window: calendar starts 2024-01 although data begins 2023-01, so the first month already has a
--         steady-state booking book (avoids a cold-start ramp).
-- Technique: recursive CTE builds a month calendar; a unit is occupied in a month if its booking
--            overlaps that month.
WITH RECURSIVE months(m) AS (
    SELECT '2024-01-01'
    UNION ALL
    SELECT date(m, '+1 month') FROM months WHERE m < '2025-12-01'
),
unit_city AS (
    SELECT u.unit_id, p.city_id
    FROM units u JOIN properties p ON p.property_id = u.property_id
),
city_units AS (
    SELECT city_id, COUNT(*) AS total_units FROM unit_city GROUP BY city_id
),
active AS (
    SELECT unit_id,
           start_date,
           date(start_date, '+' || duration_months || ' months') AS end_date
    FROM bookings
    WHERE status IN ('Confirmed', 'Completed')
)
SELECT c.city,
       strftime('%Y-%m', m.m)                       AS month,
       cu.total_units,
       COUNT(DISTINCT a.unit_id)                    AS occupied_units,
       ROUND(100.0 * COUNT(DISTINCT a.unit_id) / cu.total_units, 1) AS occupancy_pct
FROM months m
CROSS JOIN cities c
JOIN city_units cu ON cu.city_id = c.city_id
LEFT JOIN unit_city uc ON uc.city_id = c.city_id
LEFT JOIN active a ON a.unit_id = uc.unit_id
                  AND a.start_date < date(m.m, '+1 month')
                  AND a.end_date   > m.m
GROUP BY c.city_id, m.m
ORDER BY c.city, m.m;
