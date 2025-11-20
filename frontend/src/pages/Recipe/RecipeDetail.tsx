import { useEffect } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import Navbar from "../../components/Navbar";

type Recipe = {
  title?: string;
  name?: string;
  cuisine?: string;
  dietary_tags?: string[];
  summary?: string;
  description?: string;
  ingredients?: string[] | string;
  ingredient_tags?: string[];
  flavour_tags?: string[];
  technique_tags?: string[];
  rating?: number | string;
  rating_count?: number;
  score?: number;
  slug?: string;
  id?: string | number;
  steps?: string[] | string;
  images?: string[] | string;
  nutrition?: unknown;
  source_url?: string;
};

const toList = (value?: string[] | string): string[] => {
  if (!value) return [];
  if (Array.isArray(value)) return value.filter(Boolean);
  return value
    .split(/[,;]+/)
    .map((item) => item.trim())
    .filter(Boolean);
};

const normalizeUrl = (url?: string): string | undefined => {
  if (!url) return undefined;
  if (url.startsWith("http://") || url.startsWith("https://")) return url;
  return `https://${url}`;
};

export default function RecipeDetail() {
  const navigate = useNavigate();
  const { slug } = useParams();
  const location = useLocation();
  const state = location.state as { recipe?: Recipe } | undefined;
  const recipe = state?.recipe;

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, [slug]);

  const title = recipe?.title || recipe?.name || "Recipe";
  const description =
    recipe?.description ||
    recipe?.summary ||
    "Delicious recipe tailored to your taste profile.";

  const ingredients =
    toList(recipe?.ingredients) || toList(recipe?.ingredient_tags);
  const steps = toList(recipe?.steps);
  const images = toList(recipe?.images);

  const dietaryTags = recipe?.dietary_tags?.filter(Boolean) ?? [];
  const flavourTags = recipe?.flavour_tags?.filter(Boolean) ?? [];
  const techniqueTags = recipe?.technique_tags?.filter(Boolean) ?? [];

  const score =
    typeof recipe?.score === "number"
      ? `Match: ${(recipe.score * 100).toFixed(0)}%`
      : null;

  if (!recipe) {
    return (
      <>
        <Navbar />
        <main className="min-h-[calc(100vh-4rem)] bg-gradient-to-b from-orange-50/80 via-orange-50 to-white pb-16">
          <div className="mx-auto w-full max-w-5xl px-6 pt-12">
            <div className="rounded-3xl border border-orange-100 bg-white px-6 py-10 text-center shadow-[0_20px_50px_rgba(249,115,22,0.08)]">
              <p className="text-lg font-semibold text-slate-700">
                Recipe details are unavailable.
              </p>
              <p className="mt-2 text-sm text-slate-500">
                Please return to the search results and open a recipe again.
              </p>
              <button
                type="button"
                onClick={() => navigate("/home")}
                className="mt-6 inline-flex items-center rounded-xl bg-orange-500 px-4 py-3 text-sm font-semibold text-white transition hover:bg-orange-600 focus:outline-none focus:ring-2 focus:ring-orange-200"
              >
                Back to Search
              </button>
            </div>
          </div>
        </main>
      </>
    );
  }

  return (
    <>
      <Navbar />
      <main className="min-h-[calc(100vh-4rem)] bg-gradient-to-b from-orange-50/80 via-orange-50 to-white pb-16">
        <div className="mx-auto w-full max-w-5xl px-6 pt-12 space-y-8">
          <div className="flex items-center justify-between gap-4">
            <button
              type="button"
              onClick={() => navigate(-1)}
              className="inline-flex items-center rounded-xl border border-orange-100 bg-white px-4 py-2 text-sm font-semibold text-orange-600 shadow-sm transition hover:border-orange-200 hover:shadow"
            >
              ← Back
            </button>
            {score ? (
              <span className="inline-flex items-center rounded-full bg-orange-100 px-3 py-1 text-xs font-semibold text-orange-700">
                {score}
              </span>
            ) : null}
          </div>

          <header className="rounded-3xl border border-orange-100 bg-white px-8 py-10 shadow-[0_25px_60px_rgba(249,115,22,0.07)]">
            <div className="space-y-4">
              <div className="flex flex-wrap items-center gap-3">
                <h1 className="text-2xl font-semibold text-slate-800">
                  {title}
                </h1>
                {recipe?.source_url ? (
                  <a
                    href={normalizeUrl(recipe.source_url)}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center rounded-full bg-orange-50 px-3 py-1 text-xs font-semibold text-orange-600 hover:bg-orange-100"
                  >
                    View Source ↗
                  </a>
                ) : null}
              </div>
              <p className="text-sm text-slate-600 leading-relaxed">{description}</p>
              <div className="flex flex-wrap gap-2">
                {(dietaryTags.length ? dietaryTags : ["Any diet"]).map((tag) => (
                  <span
                    key={`diet-${tag}`}
                    className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600"
                  >
                    {tag}
                  </span>
                ))}
                {flavourTags.slice(0, 3).map((tag) => (
                  <span
                    key={`flav-${tag}`}
                    className="rounded-full bg-orange-50 px-3 py-1 text-xs font-semibold text-orange-600"
                  >
                    {tag}
                  </span>
                ))}
                {techniqueTags.slice(0, 2).map((tag) => (
                  <span
                    key={`tech-${tag}`}
                    className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-600"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          </header>

          <section className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            <div className="rounded-3xl border border-orange-100 bg-white px-6 py-6 shadow-sm lg:col-span-2 space-y-6">
              <div>
                <h2 className="text-base font-semibold text-slate-800">
                  Steps
                </h2>
                <ol className="mt-3 space-y-3 text-sm text-slate-700 list-decimal list-inside">
                  {steps.length ? (
                    steps.map((step, idx) => <li key={`${idx}-${step}`}>{step}</li>)
                  ) : (
                    <li className="text-slate-500 list-none">
                      Steps coming soon.
                    </li>
                  )}
                </ol>
              </div>
            </div>

            <div className="rounded-3xl border border-orange-100 bg-white px-6 py-6 shadow-sm">
              <h2 className="text-base font-semibold text-slate-800">
                Details
              </h2>
              <div className="mt-3 space-y-2 text-sm text-slate-600">
                <div className="flex justify-between">
                  <span className="text-slate-500">Diet</span>
                  <span className="font-medium">
                    {dietaryTags.length ? dietaryTags.join(", ") : "Any"}
                  </span>
                </div>
                {recipe.cuisine ? (
                  <div className="flex justify-between">
                    <span className="text-slate-500">Cuisine</span>
                    <span className="font-medium">{recipe.cuisine}</span>
                  </div>
                ) : null}
                {recipe.rating ? (
                  <div className="flex justify-between">
                    <span className="text-slate-500">Rating</span>
                  <span className="font-medium">
                    {recipe.rating}
                    {recipe.rating_count ? ` (${recipe.rating_count})` : ""}
                  </span>
                </div>
              ) : null}

                <div className="mt-4">
                  <p className="text-sm font-semibold text-slate-800">Ingredients</p>
                  <ul className="mt-2 space-y-2 text-sm text-slate-700">
                    {ingredients.length ? (
                      ingredients.map((item, idx) => (
                        <li key={`${item}-${idx}`} className="flex gap-2">
                          <span className="mt-[6px] h-1.5 w-1.5 rounded-full bg-orange-400" />
                          <span>{item}</span>
                        </li>
                      ))
                    ) : (
                      <li className="text-slate-500">Ingredients coming soon.</li>
                    )}
                  </ul>
                </div>

                {recipe.nutrition ? (
                  <div className="mt-3 space-y-1">
                    <p className="text-sm font-semibold text-slate-800">Nutrition</p>
                    {typeof recipe.nutrition === "string" ? (
                      <p className="text-sm text-slate-600">{recipe.nutrition}</p>
                    ) : Array.isArray(recipe.nutrition) ? (
                      <ul className="space-y-1 text-sm text-slate-600 list-disc list-inside">
                        {recipe.nutrition.map((item, idx) => (
                          <li key={`nut-${idx}`}>{String(item)}</li>
                        ))}
                      </ul>
                    ) : typeof recipe.nutrition === "object" ? (
                      <ul className="space-y-1 text-sm text-slate-600">
                        {Object.entries(recipe.nutrition as Record<string, unknown>).map(
                          ([key, val]) => (
                            <li key={`nut-${key}`} className="flex justify-between gap-3">
                              <span className="text-slate-500">{key}</span>
                              <span className="font-medium">{String(val)}</span>
                            </li>
                          )
                        )}
                      </ul>
                    ) : null}
                  </div>
                ) : null}
              </div>
            </div>
          </section>

          {images.length ? (
            <section className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              {images.map((src, idx) => (
                <div
                  key={`${src}-${idx}`}
                  className="overflow-hidden rounded-2xl border border-orange-100 bg-white shadow-sm"
                >
                  <img
                    src={src}
                    alt={title}
                    className="h-64 w-full object-cover"
                    loading="lazy"
                  />
                </div>
              ))}
            </section>
          ) : null}
        </div>
      </main>
    </>
  );
}
