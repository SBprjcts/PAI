-- Database/import_seed.sql  (psql-only)
\pset pager off

\set seed_email 'seed@system.local'
\set seed_company 'Seed Company'
\set seed_password 'seed-password'

-- Ensure a seed user exists and capture its id into :seed_user_id
WITH existing AS (
  SELECT id FROM users WHERE email = :'seed_email' LIMIT 1
),
inserted AS (
  INSERT INTO users (id, company, email, password)
  SELECT
    (SELECT COALESCE(MAX(id),0)+1 FROM users),  -- next id if table has no sequence
    :'seed_company',
    :'seed_email',
    :'seed_password'
  WHERE NOT EXISTS (SELECT 1 FROM existing)
  RETURNING id
)
SELECT id AS seed_user_id FROM inserted
UNION ALL
SELECT id AS seed_user_id FROM existing
LIMIT 1;
\gset

\echo Using seed user_id = :seed_user_id

BEGIN;

-- Raw staging in CSV order: vendor,description,category,date,amount
DROP TABLE IF EXISTS staging_raw;
CREATE TABLE staging_raw (
  vendor       text,
  description  text,
  category     text,
  date_txt     text,
  amount_txt   text
);

-- ONE LINE, adjust path if needed
\copy staging_raw FROM 'C:/Users/saifb/Downloads/PAI/data/training_data.csv' WITH (FORMAT csv, HEADER true)

-- Insert into real table with proper types
INSERT INTO expenses (user_id, expense_date, amount, vendor, description, category)
SELECT
  :seed_user_id,
  CASE
    WHEN date_txt ~ '^\d{4}-\d{2}-\d{2}$' THEN date_txt::date
    WHEN date_txt ~ '^\d{1,2}/\d{1,2}/\d{4}$' THEN to_date(date_txt, 'MM/DD/YYYY')
    ELSE NULL
  END,
  NULLIF(regexp_replace(amount_txt, '[^0-9.\-]', '', 'g'), '')::numeric(12,2),
  vendor,
  description,
  category
FROM staging_raw;

DROP TABLE staging_raw;

COMMIT;

