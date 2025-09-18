INSERT INTO user (
    id,
    company,
    email,
    password,
    expense_ids,
) VALUES (%s, %s, %s, %s, %s);
