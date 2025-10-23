SELECT title, cuisine, rating_avg
FROM recipe_metadata
WHERE cuisine ILIKE $1
ORDER BY rating_avg DESC
LIMIT 10;