-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_userprefs_userid ON user_prefs(user_id);
CREATE INDEX IF NOT EXISTS idx_recipe_cuisine ON recipe_metadata(cuisine);
CREATE INDEX IF NOT EXISTS idx_recipe_rating ON recipe_metadata(rating_avg);

-- Unique constraint to ensure no duplicate MongoDB IDs in recipe_metadata
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'unique_recipe_mongo'
          AND conrelid = 'recipe_metadata'::regclass
    ) THEN
        ALTER TABLE recipe_metadata
        ADD CONSTRAINT unique_recipe_mongo UNIQUE (mongo_id);
    END IF;
END
$$;
