"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export function LoginForm({
  className,
  ...props
}: React.ComponentProps<"div">) {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!email.trim() || !password.trim()) {
      setError("Please fill in all fields.");
      return;
    }

    setLoading(true);

    try {
      // Check if user exists in localStorage
      const usersRaw = localStorage.getItem("synaptiq_users");
      const users: { name: string; email: string; password: string }[] = usersRaw
        ? JSON.parse(usersRaw)
        : [];

      const user = users.find(
        (u) => u.email.toLowerCase() === email.toLowerCase() && u.password === password
      );

      if (!user) {
        setError("Invalid email or password.");
        setLoading(false);
        return;
      }

      // Save session
      localStorage.setItem(
        "synaptiq_session",
        JSON.stringify({ name: user.name, email: user.email, loggedInAt: Date.now() })
      );

      // Redirect to dashboard
      router.push("/dashboard");
    } catch {
      setError("Something went wrong. Please try again.");
      setLoading(false);
    }
  };

  return (
    <div className={cn("flex flex-col gap-6", className)} {...props}>
      {/* Logo + heading */}
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br from-cyan-400 to-blue-500 mb-4 shadow-[0_0_24px_rgba(6,182,212,0.35)]">
          <svg className="w-6 h-6 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 2a4 4 0 0 1 4 4c0 1.95-1.4 3.58-3.25 3.93" />
            <path d="M8.56 13.44A4 4 0 1 0 12 18" />
            <path d="M12 18a4 4 0 0 0 4-4c0-1.1-.45-2.1-1.17-2.83" />
            <circle cx="12" cy="12" r="1.5" fill="currentColor" />
          </svg>
        </div>
        <h1 className="text-2xl font-bold text-slate-900">Welcome back</h1>
        <p className="text-sm text-slate-500 mt-1">Sign in to your account</p>
      </div>

      {/* Glass card */}
      <div
        className="rounded-2xl p-6 space-y-4"
        style={{
          background: "rgba(255,255,255,0.75)",
          backdropFilter: "blur(24px) saturate(1.8)",
          border: "1px solid rgba(255,255,255,0.9)",
          boxShadow: "0 8px 32px rgba(0,0,0,0.08), inset 0 1px 0 rgba(255,255,255,0.9)",
        }}
      >
        <form className="space-y-4" onSubmit={handleSubmit}>
          {error && (
            <div className="rounded-lg px-3 py-2 text-sm font-medium text-red-700 bg-red-50 border border-red-200">
              {error}
            </div>
          )}

          <div className="space-y-1.5">
            <Label htmlFor="email" className="text-sm text-slate-600">Email</Label>
            <Input
              id="email"
              type="email"
              placeholder="you@example.com"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="bg-white border-slate-200 text-slate-800 placeholder:text-slate-400 focus-visible:ring-cyan-400/50 focus-visible:border-cyan-400/60"
            />
          </div>

          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <Label htmlFor="password" className="text-sm text-slate-600">Password</Label>
              <a href="#" className="text-xs text-cyan-600 hover:text-cyan-500 transition-colors">
                Forgot password?
              </a>
            </div>
            <Input
              id="password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="bg-white border-slate-200 text-slate-800 placeholder:text-slate-400 focus-visible:ring-cyan-400/50 focus-visible:border-cyan-400/60"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 rounded-md text-sm font-semibold text-white transition-all duration-300 hover:scale-[1.01] hover:brightness-110 disabled:opacity-60 disabled:cursor-not-allowed"
            style={{
              background: "linear-gradient(135deg, #3b82f6, #1d4ed8)",
              boxShadow: "0 0 16px rgba(59,130,246,0.40)",
            }}
          >
            {loading ? "Signing in..." : "Sign In"}
          </button>

          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t border-slate-200" />
            </div>
            <div className="relative flex justify-center text-xs">
              <span className="px-3 bg-white/0 text-slate-400">or continue with</span>
            </div>
          </div>

          <button
            type="button"
            className="w-full flex items-center justify-center gap-2 py-2.5 rounded-md border border-slate-200 bg-white text-slate-600 text-sm font-medium hover:bg-slate-50 hover:text-slate-800 transition-all duration-300"
          >
            <svg className="w-4 h-4" viewBox="0 0 24 24">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
            </svg>
            Continue with Google
          </button>
        </form>
      </div>

      <p className="text-center text-sm text-slate-500">
        Don&apos;t have an account?{" "}
        <Link href="/signup" className="text-cyan-600 hover:text-cyan-500 font-medium transition-colors">
          Sign up
        </Link>
      </p>
    </div>
  );
}
