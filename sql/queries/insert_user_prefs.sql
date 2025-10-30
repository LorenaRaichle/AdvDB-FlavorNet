INSERT INTO user_prefs (user_id, diet_type, allergies, dislikes)
VALUES (:user_id, :diet_type, :allergies, :dislikes)
RETURNING *;