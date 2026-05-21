"use client";

import { useEffect, useState } from "react";
import { onAuthStateChanged, signOut, type User } from "firebase/auth";
import { auth } from "@/lib/firebase";

export function UserMenu() {
  const [firebaseUser, setFirebaseUser] = useState<User | null>(null);

  useEffect(() => {
    return onAuthStateChanged(auth, setFirebaseUser);
  }, []);

  if (!firebaseUser) {
    return (
      <a href="/login" className="text-sm underline">
        Sign in
      </a>
    );
  }

  return (
    <div className="flex items-center gap-3 text-sm">
      <span>{firebaseUser.email}</span>

      <button
        type="button"
        onClick={() => signOut(auth)}
        className="rounded border px-3 py-1"
      >
        Sign out
      </button>
    </div>
  );
}
