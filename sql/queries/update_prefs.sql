UPDATE user_prefs
SET diet_type = $2,
    allergies = $3,
    dislikes = $4,
    updated_at = CURRENT_TIMESTAMP
WHERE user_id = $1
RETURNING *;