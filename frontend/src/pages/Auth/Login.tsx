import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import AuthLayout from "../../components/AuthLayout";
import { useUserStore } from "../../store/userStore";
import { listUsers } from "../../api/users.api";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const setUser = useUserStore((state) => state.setUser);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);
    try {
      const response = await listUsers();
      const users = Array.isArray(response.data) ? response.data : [];
      const matched = users.find(
        (u: any) =>
          typeof u.email === "string" &&
          u.email.toLowerCase() === email.trim().toLowerCase()
      );

      if (!matched) {
        setError("We couldn't find an account with that email.");
        return;
      }

      setUser({ id: matched.user_id, email: matched.email });
      navigate("/home");
    } catch (err) {
      console.error(err);
      setError("Logging in failed. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AuthLayout
      title="Welcome back"
      description="Log in to view your personalized recipe recommendations and manage your taste profile."
      footer={
        <p className="text-sm text-slate-500">
          New to FlavorNet?{" "}
          <Link to="/register" className="font-semibold text-orange-500">
            Create an account
          </Link>
        </p>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-5">
        <div className="space-y-2">
          <label
            htmlFor="email"
            className="block text-sm font-medium text-slate-700"
          >
            Email address
          </label>
          <input
            id="email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
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
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className="w-full rounded-lg border border-orange-100 px-4 py-3 text-sm text-slate-800 transition focus:border-orange-300 focus:outline-none focus:ring-2 focus:ring-orange-100"
            placeholder="********"
          />
        </div>

        {error && (
          <p className="rounded-lg border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-600">
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={isSubmitting}
          className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-orange-500 px-4 py-3 text-sm font-semibold text-white transition hover:bg-orange-600 focus:outline-none focus:ring-2 focus:ring-orange-200 disabled:cursor-not-allowed disabled:bg-orange-300"
        >
          {isSubmitting ? "Signing in..." : "Log in"}
        </button>
        <p className="text-xs text-slate-400">
          Password verification isn&apos;t wired yet; we match accounts by email
          for now.
        </p>
      </form>
    </AuthLayout>
  );
}
