CREATE INDEX IF NOT EXISTS idx_expenses_user_date
  ON expenses(user_id, expense_date);

CREATE INDEX IF NOT EXISTS idx_labels_expense
  ON user_labels(expense_id);

ALTER TABLE user_labels
  ADD CONSTRAINT unique_user_expense UNIQUE (user_id, expense_id);


