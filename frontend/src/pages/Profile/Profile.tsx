import { useEffect, useMemo, useState } from "react";
import Navbar from "../../components/Navbar";
import TagInput from "../../components/TagInput";
import {
  getUserPrefs,
  updateUserPrefs,
  clearUserPrefs,
} from "../../api/users.api";
import { useUserStore } from "../../store/userStore";

type Preferences = {
  diet_type: string[];
  allergies: string[];
  dislikes: string[];
};

const emptyPreferences: Preferences = {
  diet_type: [],
  allergies: [],
  dislikes: [],
};

export default function Profile() {
  const { user } = useUserStore();
  const [prefs, setPrefs] = useState<Preferences>(emptyPreferences);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [isClearing, setIsClearing] = useState<boolean>(false);
  const [feedback, setFeedback] = useState<{
    type: "success" | "error";
    message: string;
  } | null>(null);

  useEffect(() => {
    const loadPrefs = async () => {
      if (!user) {
        setIsLoading(false);
        return;
      }
      setIsLoading(true);
      setFeedback(null);
      try {
        const response = await getUserPrefs(user.id);
        const data = response.data || {};
        setPrefs({
          diet_type: Array.isArray(data.diet_type) ? data.diet_type : [],
          allergies: Array.isArray(data.allergies) ? data.allergies : [],
          dislikes: Array.isArray(data.dislikes) ? data.dislikes : [],
        });
      } catch (error) {
        console.error(error);
        setFeedback({
          type: "error",
          message: "We couldn't load your preferences. Please try again.",
        });
      } finally {
        setIsLoading(false);
      }
    };

    loadPrefs();
  }, [user]);

  const updateField = (field: keyof Preferences) => (values: string[]) => {
    setPrefs((prev) => ({
      ...prev,
      [field]: values,
    }));
  };

  const handleSave = async () => {
    if (!user) return;
    setIsSaving(true);
    setFeedback(null);
    try {
      await updateUserPrefs(user.id, prefs);
      setFeedback({
        type: "success",
        message: "Preferences updated successfully.",
      });
    } catch (error) {
      console.error(error);
      setFeedback({
        type: "error",
        message: "Updating your preferences failed. Please try again.",
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleClear = async () => {
    if (!user) return;
    setIsClearing(true);
    setFeedback(null);
    try {
      await clearUserPrefs(user.id);
      setPrefs(emptyPreferences);
      setFeedback({
        type: "success",
        message: "All preferences cleared.",
      });
    } catch (error) {
      console.error(error);
      setFeedback({
        type: "error",
        message: "We couldn't clear your preferences. Please try again.",
      });
    } finally {
      setIsClearing(false);
    }
  };

  const title = useMemo(() => {
    if (!user) {
      return "Sign in to view preferences";
    }
    return "Edit your taste profile";
  }, [user]);

  return (
    <>
      <Navbar />
      <main className="mx-auto w-full max-w-4xl px-6 py-10">
        <section className="rounded-3xl border border-orange-100 bg-white px-8 py-10 shadow-[0_25px_60px_rgba(249,115,22,0.05)]">
          <div className="space-y-2">
            <h1 className="text-3xl font-semibold text-slate-800">{title}</h1>
            <p className="text-sm text-slate-500">
              Adjust your diet styles, allergies, and dislikes to keep your
              recommendations on point.
            </p>
          </div>
          {!user ? (
            <div className="mt-10 rounded-2xl border border-orange-100 bg-orange-50/70 px-6 py-10 text-center text-sm text-orange-600">
              Log in to manage your preferences and keep your recommendations in
              sync across devices.
            </div>
          ) : (
            <div className="mt-10 space-y-8">
              {isLoading ? (
                <div className="flex h-40 items-center justify-center rounded-2xl border border-dashed border-orange-200 bg-orange-50/60">
                  <div className="flex items-center gap-3 text-sm font-medium text-orange-500">
                    <span className="h-4 w-4 animate-spin rounded-full border-2 border-orange-400 border-t-transparent" />
                    Loading your preferences...
                  </div>
                </div>
              ) : (
                <>
                  <div className="grid gap-6">
                    <TagInput
                      label="Diet styles"
                      values={prefs.diet_type}
                      onChange={updateField("diet_type")}
                      placeholder="Vegetarian, Vegan, Keto..."
                    />
                    <TagInput
                      label="Allergies to avoid"
                      values={prefs.allergies}
                      onChange={updateField("allergies")}
                      placeholder="Peanuts, Shellfish..."
                    />
                    <TagInput
                      label="Ingredients you dislike"
                      values={prefs.dislikes}
                      onChange={updateField("dislikes")}
                      placeholder="Cilantro, Mushrooms..."
                    />
                  </div>

                  {feedback && (
                    <div
                      className={[
                        "rounded-xl px-4 py-3 text-sm",
                        feedback.type === "success"
                          ? "border border-orange-100 bg-orange-50 text-orange-600"
                          : "border border-red-100 bg-red-50 text-red-600",
                      ].join(" ")}
                    >
                      {feedback.message}
                    </div>
                  )}

                  <div className="flex flex-col gap-3 sm:flex-row sm:justify-end">
                    <button
                      type="button"
                      onClick={handleClear}
                      disabled={isClearing || isSaving}
                      className="inline-flex items-center justify-center rounded-xl border border-orange-200 bg-white px-5 py-3 text-sm font-semibold text-orange-500 transition hover:border-orange-300 hover:text-orange-600 focus:outline-none focus:ring-2 focus:ring-orange-200 disabled:cursor-not-allowed disabled:opacity-70"
                    >
                      {isClearing ? "Clearing..." : "Clear Preferences"}
                    </button>
                    <button
                      type="button"
                      onClick={handleSave}
                      disabled={isSaving || isClearing}
                      className="inline-flex items-center justify-center rounded-xl bg-orange-500 px-5 py-3 text-sm font-semibold text-white transition hover:bg-orange-600 focus:outline-none focus:ring-2 focus:ring-orange-200 disabled:cursor-not-allowed disabled:bg-orange-300"
                    >
                      {isSaving ? "Saving..." : "Save Changes"}
                    </button>
                  </div>
                </>
              )}
            </div>
          )}
        </section>
      </main>
    </>
  );
}
