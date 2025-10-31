import type { ReactNode } from "react";

interface AuthLayoutProps {
  title: string;
  description?: string;
  children: ReactNode;
  footer?: ReactNode;
  contentScrollable?: boolean;
}

export default function AuthLayout({
  title,
  description,
  children,
  footer,
  contentScrollable = false,
}: AuthLayoutProps) {
  return (
    <div className="h-screen overflow-hidden bg-gradient-to-br from-orange-50 via-white to-orange-100 px-6 py-6">
      <div className="mx-auto flex h-full w-full max-w-5xl items-center justify-center">
        <div className="grid h-full w-full gap-10 overflow-hidden rounded-3xl bg-white/70 p-8 shadow-[0_30px_80px_rgba(249,115,22,0.12)] backdrop-blur lg:grid-cols-[1fr_1.1fr]">
          <div className="hidden h-full rounded-2xl bg-gradient-to-br from-orange-500 via-orange-600 to-orange-700 p-10 text-white lg:flex lg:flex-col lg:justify-between">
            <div className="space-y-6">
              <p className="inline-flex items-center gap-2 rounded-full bg-white/15 px-4 py-1 text-sm font-medium uppercase tracking-[0.2em]">
                FlavorNet
              </p>
              <div className="space-y-4">
                <h2 className="text-4xl font-semibold leading-tight">
                  Discover recipes tailored to your taste.
                </h2>
                <p className="text-base text-orange-50/80">
                  Tell us your preferences and we will surface recipes that fit
                  your flavor profile. Seamlessly explore cuisines, find new
                  favorites, and keep track of what you love.
                </p>
              </div>
            </div>
            <div className="space-y-2">
              <p className="text-sm font-semibold uppercase tracking-wider text-orange-100/80">
                Why FlavorNet?
              </p>
              <ul className="space-y-2 text-sm text-orange-50/80">
                <li>• Smart matches for your taste buds</li>
                <li>• Track dietary needs without the hassle</li>
                <li>• Curated ideas from cuisines you care about</li>
              </ul>
            </div>
          </div>
          <div className="flex h-full flex-col overflow-hidden rounded-2xl border border-orange-100 bg-white/95 p-8 shadow-xl">
            <div>
              <h1 className="text-3xl font-semibold text-slate-800">{title}</h1>
              {description && (
                <p className="mt-2 text-sm text-slate-500">{description}</p>
              )}
            </div>
            <div
              className={[
                "mt-8",
                contentScrollable
                  ? "flex-1 overflow-y-auto pr-2"
                  : "space-y-6",
              ].join(" ")}
            >
              {contentScrollable ? (
                <div className="space-y-6 pb-6">{children}</div>
              ) : (
                children
              )}
            </div>
            {footer && (
              <div className={["mt-10", contentScrollable ? "pt-4" : ""].join(" ")}>
                {footer}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
