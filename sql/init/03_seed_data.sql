-- Users
INSERT INTO users (email, password_hash)
VALUES 
('test@example.com', 'hashedpassword123'),
('admin@example.com', 'supersecurehash')
ON CONFLICT DO NOTHING;

-- User Preferences
INSERT INTO user_prefs (user_id, diet_type, allergies, dislikes)
VALUES 
(1, 'vegan', ARRAY['milk', 'nuts'], ARRAY['onion']),
(2, 'halal', ARRAY['pork'], ARRAY['alcohol']);

-- Recipes (linked to MongoDB)
INSERT INTO recipe_metadata (mongo_id, title, cuisine, rating_avg)
VALUES
('abc123', 'Vegan Spaghetti', 'Italian', 4.8),
('xyz456', 'Halal Chicken Curry', 'Indian', 4.5);