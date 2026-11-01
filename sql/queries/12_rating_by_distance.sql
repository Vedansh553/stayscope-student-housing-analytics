-- Q12: Review rating vs distance from campus
-- Business question: Does proximity drive satisfaction?
-- Caution: only ~45% of completed stays leave a review, so n matters.
SELECT CASE WHEN p.distance_km < 2 THEN '1. < 2 km'
            WHEN p.distance_km < 5 THEN '2. 2-5 km'
            ELSE '3. 5+ km' END        AS distance_band,
       COUNT(*)                        AS reviews,
       ROUND(AVG(r.rating), 2)         AS avg_rating,
       ROUND(100.0 * AVG(CASE WHEN r.rating <= 2 THEN 1.0 ELSE 0 END), 1) AS low_rating_pct
FROM reviews r
JOIN bookings b   ON b.booking_id = r.booking_id
JOIN units u      ON u.unit_id = b.unit_id
JOIN properties p ON p.property_id = u.property_id
GROUP BY distance_band
ORDER BY distance_band;
