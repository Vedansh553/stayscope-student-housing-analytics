-- Q09: Rent vs distance from campus, normalised within city
-- Business question: How much of a premium do students pay for proximity?
-- Index = unit rent / average unit rent in the same city (window function), so cities with
-- very different price levels can be compared on one axis.
WITH unit_detail AS (
    SELECT u.unit_id,
           p.city_id,
           p.distance_km,
           u.monthly_rent_usd,
           u.monthly_rent_usd / AVG(u.monthly_rent_usd) OVER (PARTITION BY p.city_id) AS rent_index
    FROM units u
    JOIN properties p ON p.property_id = u.property_id
)
SELECT CASE WHEN distance_km < 1 THEN '1. < 1 km'
            WHEN distance_km < 2 THEN '2. 1-2 km'
            WHEN distance_km < 4 THEN '3. 2-4 km'
            WHEN distance_km < 7 THEN '4. 4-7 km'
            ELSE '5. 7+ km' END           AS distance_band,
       COUNT(*)                           AS units,
       ROUND(AVG(rent_index), 3)          AS avg_rent_index
FROM unit_detail
GROUP BY distance_band
ORDER BY distance_band;
