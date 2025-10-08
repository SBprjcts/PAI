INSERT INTO expense (
    id,
    date,
    amount,
    vendor,
    description,
    category,
    anomaly_score
) VALUES (%s, %s, %s, %s, %s, %s, %s);
