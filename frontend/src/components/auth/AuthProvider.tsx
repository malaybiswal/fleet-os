"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { onAuthStateChanged, type User } from "firebase/auth";
import { auth } from "@/lib/firebase";
import { getCurrentUser, type CurrentUser } from "@/lib/api";

type AuthContextValue = {
  firebaseUser: User | null;
  currentUser: CurrentUser | null;
  isLoading: boolean;
  isAuthenticated: boolean;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [firebaseUser, setFirebaseUser] = useState<User | null>(null);
  const [currentUser, setCurrentUser] = useState<CurrentUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    return onAuthStateChanged(auth, async (user) => {
      setFirebaseUser(user);

      if (!user) {
        setCurrentUser(null);
        setIsLoading(false);
        return;
      }

      try {
        const me = await getCurrentUser();
        setCurrentUser(me);
      } catch (error) {
        console.error("Failed to load current user", error);
        setCurrentUser(null);
      } finally {
        setIsLoading(false);
      }
    });
  }, []);

  const value = useMemo(
    () => ({
      firebaseUser,
      currentUser,
      isLoading,
      isAuthenticated: Boolean(firebaseUser && currentUser),
    }),
    [firebaseUser, currentUser, isLoading],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);

  if (!value) {
    throw new Error("useAuth must be used inside AuthProvider");
  }

  return value;
}