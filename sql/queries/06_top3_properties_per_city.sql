-- Q06: Top 3 properties per city by retained GMV
-- Business question: Which properties anchor each city's revenue?
WITH prop_gmv AS (
    SELECT p.city_id,
           p.property_id,
           p.property_type,
           p.distance_km,
           COUNT(*)                                          AS bookings,
           ROUND(SUM(b.monthly_rent_usd * b.duration_months), 0) AS gmv_usd
    FROM bookings b
    JOIN units u       ON u.unit_id = b.unit_id
    JOIN properties p  ON p.property_id = u.property_id
    WHERE b.status IN ('Confirmed', 'Completed')
    GROUP BY p.property_id
),
ranked AS (
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY city_id ORDER BY gmv_usd DESC, property_id) AS rn
    FROM prop_gmv
)
SELECT c.city, r.rn AS rank_in_city, r.property_id, r.property_type, r.distance_km, r.bookings, r.gmv_usd
FROM ranked r
JOIN cities c ON c.city_id = r.city_id
WHERE r.rn <= 3
ORDER BY c.city, r.rn;
