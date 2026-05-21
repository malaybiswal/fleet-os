"use client";
export const dynamic = "force-dynamic";

import { useState } from "react";
import { signInWithPopup } from "firebase/auth";
import { auth, googleProvider } from "@/lib/firebase";

export default function LoginPage() {
  const [error, setError] = useState<string | null>(null);
  const [isSigningIn, setIsSigningIn] = useState(false);

  async function handleGoogleLogin() {
    setError(null);
    setIsSigningIn(true);

    try {
      const result = await signInWithPopup(auth, googleProvider);
      const token = await result.user.getIdToken();

      console.log("Firebase ID token:", token);

      window.location.href = "/";
    } catch (err) {
      console.error(err);
      setError("Google login failed. Please try again.");
    } finally {
      setIsSigningIn(false);
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center p-6">
      <div className="w-full max-w-md rounded-xl border p-6 shadow-sm">
        <h1 className="text-2xl font-semibold mb-2">Sign in to FleetOS</h1>

        <p className="text-sm text-gray-600 mb-6">
          Use your Google account to access your fleet dashboard.
        </p>

        <button
          type="button"
          onClick={handleGoogleLogin}
          disabled={isSigningIn}
          className="w-full rounded-lg border px-4 py-2 font-medium disabled:opacity-60"
        >
          {isSigningIn ? "Signing in..." : "Continue with Google"}
        </button>

        {error && (
          <p className="mt-4 text-sm text-red-600">
            {error}
          </p>
        )}
      </div>
    </main>
  );
}