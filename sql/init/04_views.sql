-- Simple view combining user + prefs
CREATE OR REPLACE VIEW user_profile_view AS
SELECT 
    u.user_id,
    u.email,
    p.diet_type,
    p.allergies,
    p.dislikes,
    u.created_at
FROM users u
LEFT JOIN user_prefs p ON u.user_id = p.user_id;

-- Aggregated stats
CREATE OR REPLACE VIEW recipe_stats_view AS
SELECT
    cuisine,
    COUNT(*) AS recipe_count,
    ROUND(AVG(rating_avg), 2) AS avg_rating
FROM recipe_metadata
GROUP BY cuisine;
