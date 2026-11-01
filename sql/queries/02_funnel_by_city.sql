-- Q02: Lead -> visit -> booking funnel by city
-- Business question: Where does the funnel leak, city by city?
SELECT c.city,
       c.country,
       COUNT(*)                                          AS leads,
       SUM(l.visited)                                    AS visits,
       SUM(l.converted)                                  AS bookings,
       ROUND(100.0 * SUM(l.visited)   / COUNT(*), 1)     AS lead_to_visit_pct,
       ROUND(100.0 * SUM(l.converted) / NULLIF(SUM(l.visited), 0), 1) AS visit_to_booking_pct,
       ROUND(100.0 * SUM(l.converted) / COUNT(*), 1)     AS lead_to_booking_pct,
       RANK() OVER (ORDER BY 1.0 * SUM(l.converted) / COUNT(*) DESC) AS conversion_rank
FROM leads l
JOIN cities c ON c.city_id = l.city_id
GROUP BY c.city_id
ORDER BY lead_to_booking_pct DESC;
