-- Q08: Demand vs supply by city (2025)
-- Business question: Where should we add inventory first?
-- Signal: leads per unit, and the share of *visited* leads that did not become a booking.
WITH units_per_city AS (
    SELECT p.city_id, COUNT(*) AS units
    FROM units u JOIN properties p ON p.property_id = u.property_id
    GROUP BY p.city_id
),
demand AS (
    SELECT city_id,
           COUNT(*)           AS leads_2025,
           SUM(visited)       AS visits_2025,
           SUM(converted)     AS bookings_2025
    FROM leads
    WHERE created_at >= '2025-01-01' AND created_at < '2026-01-01'
    GROUP BY city_id
)
SELECT c.city,
       up.units,
       d.leads_2025,
       ROUND(1.0 * d.leads_2025 / up.units, 2)                        AS leads_per_unit,
       ROUND(100.0 * (d.visits_2025 - d.bookings_2025) / d.visits_2025, 1) AS visited_not_booked_pct,
       RANK() OVER (ORDER BY 1.0 * d.leads_2025 / up.units DESC)      AS pressure_rank
FROM demand d
JOIN units_per_city up ON up.city_id = d.city_id
JOIN cities c          ON c.city_id = d.city_id
ORDER BY leads_per_unit DESC;
