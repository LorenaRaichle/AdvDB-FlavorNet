INSERT INTO users (email, password_hash)
VALUES (:email, :password_hash)
RETURNING user_id, email, created_at;