INSERT INTO expenses (
    id,
    user_id,
    expense_date,
    amount,
    vendor,
    description,
    category,
    anomaly_score
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
