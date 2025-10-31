import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import AuthLayout from "../../components/AuthLayout";
import TagInput from "../../components/TagInput";
import { registerUser } from "../../api/auth.api";

type RegisterForm = {
  email: string;
  password: string;
  diet_type: string[];
  allergies: string[];
  dislikes: string[];
};

const initialState: RegisterForm = {
  email: "",
  password: "",
  diet_type: [],
  allergies: [],
  dislikes: [],
};

export default function Register() {
  const [form, setForm] = useState<RegisterForm>(initialState);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const navigate = useNavigate();

  const handleFieldChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const updatePreferences = (
    field: keyof Omit<RegisterForm, "email" | "password">
  ) => {
    return (values: string[]) =>
      setForm((prev) => ({
        ...prev,
        [field]: values,
      }));
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setIsSubmitting(true);

    const payload = {
      email: form.email.trim(),
      password: form.password,
      diet_type: form.diet_type.length ? form.diet_type : undefined,
      allergies: form.allergies.length ? form.allergies : undefined,
      dislikes: form.dislikes.length ? form.dislikes : undefined,
    };

    try {
      await registerUser(payload);
      alert("Account created! Please log in.");
      setForm(initialState);
      navigate("/");
    } catch (error) {
      console.error(error);
      alert(
        "Something went wrong while creating your account. Please try again."
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AuthLayout
      title="Create your FlavorNet account"
      description="Tell us a bit about your preferences so we can serve the right recipes from day one."
      contentScrollable
      footer={
        <p className="text-sm text-slate-500">
          Already have an account?{" "}
          <Link to="/" className="font-semibold text-orange-500">
            Log in
          </Link>
        </p>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="space-y-2">
          <label
            htmlFor="email"
            className="block text-sm font-medium text-slate-700"
          >
            Email address
          </label>
          <input
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            required
            value={form.email}
            onChange={handleFieldChange}
            className="w-full rounded-lg border border-orange-100 px-4 py-3 text-sm text-slate-800 transition focus:border-orange-300 focus:outline-none focus:ring-2 focus:ring-orange-100"
            placeholder="you@example.com"
          />
        </div>

        <div className="space-y-2">
          <label
            htmlFor="password"
            className="block text-sm font-medium text-slate-700"
          >
            Password
          </label>
          <input
            id="password"
            name="password"
            type="password"
            autoComplete="new-password"
            required
            value={form.password}
            onChange={handleFieldChange}
            className="w-full rounded-lg border border-orange-100 px-4 py-3 text-sm text-slate-800 transition focus:border-orange-300 focus:outline-none focus:ring-2 focus:ring-orange-100"
            placeholder="Choose a strong password"
          />
        </div>

        <div className="grid gap-5 rounded-xl bg-orange-50/60 p-5">
          <p className="text-sm font-semibold uppercase tracking-wide text-slate-500">
            Optional preferences
          </p>
          <TagInput
            label="Diet styles"
            values={form.diet_type}
            onChange={updatePreferences("diet_type")}
            placeholder="Vegetarian, Keto, Mediterranean..."
          />
          <TagInput
            label="Allergies"
            values={form.allergies}
            onChange={updatePreferences("allergies")}
            placeholder="Peanuts, Shellfish..."
          />
          <TagInput
            label="Dislikes"
            values={form.dislikes}
            onChange={updatePreferences("dislikes")}
            placeholder="Cilantro, Mushrooms..."
          />
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-orange-500 px-4 py-3 text-sm font-semibold text-white transition hover:bg-orange-600 focus:outline-none focus:ring-2 focus:ring-orange-200 disabled:cursor-not-allowed disabled:bg-orange-300"
        >
          {isSubmitting ? "Creating account..." : "Create account"}
        </button>
      </form>
    </AuthLayout>
  );
}
