UPDATE user_prefs
SET diet_type = :diet_type,
    allergies = :allergies,
    dislikes = :dislikes,
    updated_at = CURRENT_TIMESTAMP
WHERE user_id = :user_id
RETURNING *;