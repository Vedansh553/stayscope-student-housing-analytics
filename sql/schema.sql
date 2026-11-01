-- StayScope schema (SQLite; portable to PostgreSQL/MySQL with minor type changes)
-- ALL DATA IS SYNTHETIC. See README for how it is generated.

DROP TABLE IF EXISTS reviews;
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS bookings;
DROP TABLE IF EXISTS leads;
DROP TABLE IF EXISTS students;
DROP TABLE IF EXISTS units;
DROP TABLE IF EXISTS properties;
DROP TABLE IF EXISTS universities;
DROP TABLE IF EXISTS cities;

CREATE TABLE cities (
    city_id      INTEGER PRIMARY KEY,
    city         TEXT NOT NULL,
    country      TEXT NOT NULL,
    currency     TEXT NOT NULL
);

CREATE TABLE universities (
    university_id INTEGER PRIMARY KEY,
    city_id       INTEGER NOT NULL REFERENCES cities(city_id),
    name          TEXT NOT NULL
);

CREATE TABLE properties (
    property_id    INTEGER PRIMARY KEY,
    city_id        INTEGER NOT NULL REFERENCES cities(city_id),
    university_id  INTEGER NOT NULL REFERENCES universities(university_id),
    property_type  TEXT NOT NULL CHECK (property_type IN ('Studio','Shared Room','Private Room','Apartment')),
    distance_km    REAL NOT NULL CHECK (distance_km >= 0),
    listed_date    TEXT NOT NULL
);

CREATE TABLE units (
    unit_id          INTEGER PRIMARY KEY,
    property_id      INTEGER NOT NULL REFERENCES properties(property_id),
    monthly_rent_usd REAL NOT NULL CHECK (monthly_rent_usd > 0)
);

CREATE TABLE students (
    student_id     INTEGER PRIMARY KEY,
    home_country   TEXT NOT NULL,
    signup_date    TEXT NOT NULL
);

CREATE TABLE leads (
    lead_id             INTEGER PRIMARY KEY,
    student_id          INTEGER NOT NULL REFERENCES students(student_id),
    city_id             INTEGER NOT NULL REFERENCES cities(city_id),
    created_at          TEXT NOT NULL,
    source              TEXT NOT NULL CHECK (source IN ('Organic','Paid Search','Social','Referral','Aggregator')),
    first_response_hrs  REAL,                -- NULL = never responded to
    visited             INTEGER NOT NULL CHECK (visited IN (0,1)),
    converted           INTEGER NOT NULL CHECK (converted IN (0,1))
);

CREATE TABLE bookings (
    booking_id      INTEGER PRIMARY KEY,
    lead_id         INTEGER NOT NULL REFERENCES leads(lead_id),
    student_id      INTEGER NOT NULL REFERENCES students(student_id),
    unit_id         INTEGER NOT NULL REFERENCES units(unit_id),
    booked_at       TEXT NOT NULL,
    start_date      TEXT NOT NULL,
    duration_months INTEGER NOT NULL CHECK (duration_months BETWEEN 3 AND 12),
    monthly_rent_usd REAL NOT NULL,
    status          TEXT NOT NULL CHECK (status IN ('Confirmed','Cancelled','Completed'))
);

CREATE TABLE payments (
    payment_id   INTEGER PRIMARY KEY,
    booking_id   INTEGER NOT NULL REFERENCES bookings(booking_id),
    attempt_no   INTEGER NOT NULL,
    method       TEXT NOT NULL CHECK (method IN ('Card','UPI','Bank Transfer','Wallet')),
    amount_usd   REAL NOT NULL,
    status       TEXT NOT NULL CHECK (status IN ('Success','Failed')),
    paid_at      TEXT NOT NULL
);

CREATE TABLE reviews (
    review_id    INTEGER PRIMARY KEY,
    booking_id   INTEGER NOT NULL REFERENCES bookings(booking_id),
    rating       INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    created_at   TEXT NOT NULL
);

CREATE INDEX idx_leads_city      ON leads(city_id);
CREATE INDEX idx_leads_created   ON leads(created_at);
CREATE INDEX idx_bookings_unit   ON bookings(unit_id);
CREATE INDEX idx_bookings_booked ON bookings(booked_at);
CREATE INDEX idx_payments_book   ON payments(booking_id);
