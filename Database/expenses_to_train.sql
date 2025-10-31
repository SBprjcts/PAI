-- Create a single view used as training data for the ML pipeline.
-- This combines user-provided labels and system "seed" labels into
-- a uniform row shape: (vendor, description, category, source).
CREATE OR REPLACE VIEW training_expenses AS
-- Rows coming from real users' labels. We only include rows where
-- the user has chosen a category (chosen_cat is not NULL).
SELECT
  vendor,
  description,
  chosen_cat AS category,    -- rename chosen_cat to category for consistency
  'user_label' AS source     -- mark source so downstream code can treat user labels specially
FROM user_labels
WHERE chosen_cat IS NOT NULL

UNION ALL

-- Rows coming from the seed dataset (initial/trusted training rows).
-- These are appended to the user labels; UNION ALL keeps duplicates if any.
SELECT
  vendor,
  description,
  category,
  'seed' AS source           -- mark these rows as seed data (system-provided)
FROM seed_expenses;

-- RUN THIS & "C:\Program Files\PostgreSQL\18\bin\psql.exe" -P pager=off "$env:PGURL" -f "C:\Users\saifb\Downloads\PAI\Database\training_view.sql"
