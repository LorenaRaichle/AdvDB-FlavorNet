import { useEffect, useMemo, useState } from "react";
import Navbar from "../../components/Navbar";
import { getTopRecipesByCuisine } from "../../api/recipes.api";

type Recipe = {
  title?: string;
  name?: string;
  cuisine?: string;
  rating_avg?: number | string;
  rating?: number | string;
  summary?: string;
  description?: string;
  ingredients?: string[] | string;
  recipe_id?: string | number;
  id?: string | number;
};

const cuisineOptions = [
  "All Cuisines",
  "Italian",
  "Mexican",
  "Mediterranean",
  "Japanese",
  "Indian",
  "Thai",
];

const difficultyOptions = ["All Difficulties", "Easy", "Medium", "Advanced"];
const timeOptions = ["Any Time", "15 min", "25 min", "40 min", "60+ min"];

const cuisineIcons: Record<string, string> = {
  italian: "🍝",
  mexican: "🌮",
  mediterranean: "🥙",
  japanese: "🍣",
  indian: "🍛",
  thai: "🍜",
  asian: "🥢",
  american: "🍔",
};

const stablePick = (key: string, values: string[]) => {
  if (values.length === 0) return "";
  if (!key) return values[0];
  const sum = key.split("").reduce((acc, char) => acc + char.charCodeAt(0), 0);
  return values[sum % values.length];
};

const formatIngredients = (ingredients?: string[] | string) => {
  if (!ingredients) return "Tailored to your saved preferences.";
  if (Array.isArray(ingredients)) return ingredients.join(", ");
  return ingredients;
};

export default function Home() {
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [query, setQuery] = useState("");
  const [selectedCuisine, setSelectedCuisine] = useState<string>(
    cuisineOptions[1]
  );
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>(
    difficultyOptions[0]
  );
  const [selectedTime, setSelectedTime] = useState<string>(timeOptions[0]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchRecipes = async (cuisine: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const cuisineParam = cuisine === "All Cuisines" ? "" : cuisine;
      const response = await getTopRecipesByCuisine(
        cuisineParam || "Italian"
      );
      setRecipes(response.data || []);
    } catch (err) {
      console.error(err);
      setError("We couldn't load recipes right now. Please try again later.");
      setRecipes([]);
    } finally {
      setIsLoading(false);
    }
  };

  const filteredRecipes = useMemo(() => {
    const searchTerm = query.trim().toLowerCase();

    return recipes.filter((recipe) => {
      const title = (recipe.title || recipe.name || "").toLowerCase();
      const cuisine = (recipe.cuisine || "").toLowerCase();

      const matchesQuery = searchTerm ? title.includes(searchTerm) : true;
      const matchesCuisine =
        selectedCuisine === "All Cuisines"
          ? true
          : cuisine === selectedCuisine.toLowerCase();

      // Difficulty and time are presentational for now.
      return matchesQuery && matchesCuisine;
    });
  }, [recipes, query, selectedCuisine]);

  const handleSearch = (event?: React.FormEvent) => {
    event?.preventDefault();
    fetchRecipes(selectedCuisine);
  };

  useEffect(() => {
    handleSearch();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedCuisine]);

  return (
    <>
      <Navbar />
      <main className="min-h-[calc(100vh-4rem)] bg-gradient-to-b from-orange-50/80 via-orange-50 to-white pb-16">
        <div className="mx-auto w-full max-w-6xl px-6 pt-10">
          <section className="rounded-3xl border border-orange-100 bg-white px-8 py-10 shadow-[0_20px_60px_rgba(249,115,22,0.08)]">
            <div className="space-y-2">
              <h1 className="text-2xl font-semibold text-slate-800">
                Find Recipes
              </h1>
              <p className="text-sm text-slate-500">
                Search your collection and discover dishes that match your taste.
              </p>
            </div>

            <form
              onSubmit={handleSearch}
              className="mt-8 space-y-4"
              role="search"
            >
              <div className="relative">
                <span className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-slate-300">
                  🔍
                </span>
                <input
                  type="search"
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="Search recipes..."
                  className="w-full rounded-2xl border border-orange-100 bg-orange-50/60 pl-12 pr-4 py-3 text-sm text-slate-700 placeholder:text-slate-400 focus:border-orange-300 focus:outline-none focus:ring-2 focus:ring-orange-100"
                />
              </div>

              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                <select
                  value={selectedCuisine}
                  onChange={(event) => setSelectedCuisine(event.target.value)}
                  className="rounded-xl border border-orange-100 bg-white px-4 py-3 text-sm text-slate-600 focus:border-orange-300 focus:outline-none focus:ring-2 focus:ring-orange-100"
                >
                  {cuisineOptions.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>

                <select
                  value={selectedDifficulty}
                  onChange={(event) => setSelectedDifficulty(event.target.value)}
                  className="rounded-xl border border-orange-100 bg-white px-4 py-3 text-sm text-slate-600 focus:border-orange-300 focus:outline-none focus:ring-2 focus:ring-orange-100"
                >
                  {difficultyOptions.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>

                <select
                  value={selectedTime}
                  onChange={(event) => setSelectedTime(event.target.value)}
                  className="rounded-xl border border-orange-100 bg-white px-4 py-3 text-sm text-slate-600 focus:border-orange-300 focus:outline-none focus:ring-2 focus:ring-orange-100"
                >
                  {timeOptions.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>

                <button
                  type="submit"
                  className="rounded-xl bg-orange-500 px-4 py-3 text-sm font-semibold text-white transition hover:bg-orange-600 focus:outline-none focus:ring-2 focus:ring-orange-200"
                >
                  Search Recipes
                </button>
              </div>
            </form>
          </section>

          <section className="mt-12">
            {isLoading ? (
              <div className="flex h-48 items-center justify-center rounded-3xl border border-dashed border-orange-200 bg-white/60">
                <div className="flex items-center gap-3 text-sm font-medium text-orange-500">
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-orange-400 border-t-transparent" />
                  Fetching delicious ideas...
                </div>
              </div>
            ) : error ? (
              <div className="rounded-3xl border border-red-100 bg-red-50/70 px-6 py-10 text-center text-sm text-red-600">
                {error}
              </div>
            ) : filteredRecipes.length === 0 ? (
              <div className="rounded-3xl border border-orange-100 bg-white px-6 py-12 text-center text-sm text-slate-500">
                No recipes matched your filters. Try adjusting your search.
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-7 md:grid-cols-2 xl:grid-cols-3">
                {filteredRecipes.map((recipe) => {
                  const title = recipe.title || recipe.name || "Untitled Recipe";
                  const cuisine = recipe.cuisine || selectedCuisine;
                  const icon =
                    cuisineIcons[cuisine.toLowerCase()] ||
                    stablePick(title, Object.values(cuisineIcons)) ||
                    "🍽️";

                  const difficulty =
                    selectedDifficulty === "All Difficulties"
                      ? stablePick(title, difficultyOptions.slice(1))
                      : selectedDifficulty;

                  const time =
                    selectedTime === "Any Time"
                      ? stablePick(title, timeOptions.slice(1))
                      : selectedTime;

                  const badges = [
                    cuisine || "Any cuisine",
                    difficulty,
                    time,
                  ];

                  const description =
                    recipe.summary ||
                    recipe.description ||
                    `Curated ${cuisine} recipe tailored to your taste profile.`;

                  return (
                    <article
                      key={String(recipe.recipe_id ?? recipe.id ?? title)}
                      className="flex h-full flex-col justify-between rounded-3xl border border-orange-100 bg-white px-7 py-8 shadow-[0_25px_50px_rgba(249,115,22,0.05)] transition hover:-translate-y-1 hover:shadow-[0_35px_60px_rgba(249,115,22,0.12)]"
                    >
                      <div className="space-y-4">
                        <span className="text-3xl">{icon}</span>
                        <div className="space-y-2">
                          <h2 className="text-lg font-semibold text-slate-800">
                            {title}
                          </h2>
                          <p className="text-sm text-slate-500">
                            {description}
                          </p>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {badges.map((badge) => (
                            <span
                              key={`${title}-${badge}`}
                              className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600"
                            >
                              {badge}
                            </span>
                          ))}
                        </div>
                        <div>
                          <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                            Ingredients
                          </p>
                          <p className="mt-1 text-sm text-slate-600">
                            {formatIngredients(recipe.ingredients)}
                          </p>
                        </div>
                      </div>
                      <div className="mt-6">
                        <button
                          type="button"
                          className="inline-flex w-full items-center justify-center rounded-xl bg-orange-500 px-4 py-3 text-sm font-semibold text-white transition hover:bg-orange-600 focus:outline-none focus:ring-2 focus:ring-orange-200"
                        >
                          View Recipe
                        </button>
                      </div>
                    </article>
                  );
                })}
              </div>
            )}
          </section>
        </div>
      </main>
    </>
  );
}
