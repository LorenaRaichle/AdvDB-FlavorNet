SELECT 
    u.email,
    COUNT(a.event_id) AS activity_count,
    MAX(a.created_at) AS last_activity
FROM users u
LEFT JOIN analytics a ON u.user_id = a.user_id
GROUP BY u.user_id, u.email
ORDER BY last_activity DESC NULLS LAST;