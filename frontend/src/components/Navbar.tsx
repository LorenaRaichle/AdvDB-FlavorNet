import { Link, NavLink, useNavigate } from "react-router-dom";
import { useUserStore } from "../store/userStore";

const navItems = [
  { label: "Search", to: "/home" },
  { label: "Profile", to: "/profile" },
];

export default function Navbar() {
  const navigate = useNavigate();
  const { user, logout } = useUserStore();

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  return (
    <nav className="sticky top-0 z-40 border-b border-orange-100 bg-white/90 backdrop-blur">
      <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-4">
        <Link
          to={user ? "/home" : "/"}
          className="flex items-center gap-3 text-xl font-semibold tracking-tight text-slate-800 transition hover:text-orange-500"
        >
          <span className="inline-flex h-9 w-9 items-center justify-center rounded-full bg-orange-100 text-lg text-orange-500">
            🍳
          </span>
          <span>FlavorNet</span>
        </Link>
        <div className="hidden items-center gap-1 md:flex">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                [
                  "rounded-full px-4 py-2 text-sm font-medium transition",
                  isActive
                    ? "text-orange-500"
                    : "text-slate-500 hover:text-orange-500",
                ].join(" ")
              }
            >
              {item.label}
            </NavLink>
          ))}
        </div>
        <div className="flex items-center gap-3">
          {user ? (
            <>
              <span className="hidden text-sm font-medium text-slate-500 sm:inline">
                {user.email}
              </span>
              <button
                onClick={handleLogout}
                className="inline-flex items-center rounded-full bg-orange-500 px-4 py-2 text-sm font-semibold text-white transition hover:bg-orange-600 focus:outline-none focus:ring-2 focus:ring-orange-200"
              >
                Logout
              </button>
            </>
          ) : (
            <Link
              to="/"
              className="inline-flex items-center rounded-full border border-orange-200 px-4 py-2 text-sm font-semibold text-orange-500 transition hover:bg-orange-50"
            >
              Log in
            </Link>
          )}
        </div>
      </div>
    </nav>
  );
}
