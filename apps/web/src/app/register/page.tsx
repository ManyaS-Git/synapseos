/* ── Register Page ─────────────────────────────────────────────────── */

"use client";

import { useState } from "react";
import Link from "next/link";
import { useRegister } from "@/hooks/use-auth";

export default function RegisterPage() {
  const [form, setForm] = useState({
    email: "",
    username: "",
    password: "",
    confirmPassword: "",
    full_name: "",
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const registerMutation = useRegister();

  const validate = () => {
    const errs: Record<string, string> = {};

    if (!form.email) errs.email = "Email is required";
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email))
      errs.email = "Invalid email format";

    if (!form.username) errs.username = "Username is required";
    else if (form.username.length < 3)
      errs.username = "Username must be at least 3 characters";
    else if (!/^[a-zA-Z0-9_-]+$/.test(form.username))
      errs.username = "Only letters, numbers, underscores, and hyphens";

    if (!form.password) errs.password = "Password is required";
    else if (form.password.length < 8) errs.password = "Must be at least 8 characters";
    else if (!/[A-Z]/.test(form.password))
      errs.password = "Must contain an uppercase letter";
    else if (!/[a-z]/.test(form.password))
      errs.password = "Must contain a lowercase letter";
    else if (!/\d/.test(form.password)) errs.password = "Must contain a number";

    if (form.password !== form.confirmPassword)
      errs.confirmPassword = "Passwords don't match";

    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    registerMutation.mutate(
      {
        email: form.email,
        username: form.username,
        password: form.password,
        full_name: form.full_name || undefined,
      },
      {
        onError: (err: Error & { detail?: string }) => {
          setErrors({ general: err.detail || "Registration failed" });
        },
      }
    );
  };

  const update = (field: string, value: string) =>
    setForm((prev) => ({ ...prev, [field]: value }));

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="w-12 h-12 rounded-xl bg-primary mx-auto flex items-center justify-center mb-4">
            <span className="text-primary-foreground font-bold text-xl">S</span>
          </div>
          <h1 className="text-2xl font-bold text-foreground">Create your account</h1>
          <p className="text-muted-foreground mt-1">Get started with SynapseOS</p>
        </div>

        {/* Form */}
        <div className="bg-card border border-border rounded-xl p-6 shadow-sm">
          <form onSubmit={handleSubmit} className="space-y-4">
            {errors.general && (
              <div className="bg-destructive/10 text-destructive text-sm px-4 py-2 rounded-lg">
                {errors.general}
              </div>
            )}

            <div>
              <label htmlFor="full_name" className="block text-sm font-medium text-foreground mb-1.5">
                Full Name <span className="text-muted-foreground">(optional)</span>
              </label>
              <input
                id="full_name"
                type="text"
                value={form.full_name}
                onChange={(e) => update("full_name", e.target.value)}
                className="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary"
                placeholder="John Doe"
              />
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-foreground mb-1.5">
                Email
              </label>
              <input
                id="email"
                type="email"
                value={form.email}
                onChange={(e) => update("email", e.target.value)}
                className="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary"
                placeholder="you@example.com"
              />
              {errors.email && (
                <p className="text-destructive text-xs mt-1">{errors.email}</p>
              )}
            </div>

            <div>
              <label htmlFor="username" className="block text-sm font-medium text-foreground mb-1.5">
                Username
              </label>
              <input
                id="username"
                type="text"
                value={form.username}
                onChange={(e) => update("username", e.target.value)}
                className="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary"
                placeholder="johndoe"
              />
              {errors.username && (
                <p className="text-destructive text-xs mt-1">{errors.username}</p>
              )}
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-foreground mb-1.5">
                Password
              </label>
              <input
                id="password"
                type="password"
                value={form.password}
                onChange={(e) => update("password", e.target.value)}
                className="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary"
                placeholder="Min. 8 characters"
              />
              {errors.password && (
                <p className="text-destructive text-xs mt-1">{errors.password}</p>
              )}
            </div>

            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-foreground mb-1.5">
                Confirm Password
              </label>
              <input
                id="confirmPassword"
                type="password"
                value={form.confirmPassword}
                onChange={(e) => update("confirmPassword", e.target.value)}
                className="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary"
                placeholder="Confirm your password"
              />
              {errors.confirmPassword && (
                <p className="text-destructive text-xs mt-1">{errors.confirmPassword}</p>
              )}
            </div>

            <button
              type="submit"
              disabled={registerMutation.isPending}
              className="w-full py-2.5 bg-primary text-primary-foreground font-medium rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {registerMutation.isPending ? "Creating account..." : "Create account"}
            </button>
          </form>

          <div className="mt-6 text-center text-sm text-muted-foreground">
            Already have an account?{" "}
            <Link href="/login" className="text-primary hover:underline font-medium">
              Sign in
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
