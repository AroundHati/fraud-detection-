"use client";

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from "react";
import { useRouter } from "next/navigation";
import { insforge } from "@/lib/insforge-client";

type User = {
  id: string;
  email: string;
  emailVerified?: boolean;
  providers?: string[];
  createdAt?: string;
  updatedAt?: string;
  profile?: { name?: string; avatar_url?: string; [key: string]: unknown };
  metadata?: Record<string, unknown>;
};

type AuthContextType = {
  user: User | null;
  loading: boolean;
  signIn: (
    email: string,
    password: string,
  ) => Promise<{ error: string | null }>;
  signUp: (
    email: string,
    password: string,
    fullName?: string,
  ) => Promise<{ error: string | null }>;
  signOut: () => Promise<void>;
  refreshUser: () => Promise<void>;
};

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  const refreshUser = useCallback(async () => {
    try {
      const { data } = await insforge.auth.getUser();
      setUser(data.user as User | null);
    } catch {
      setUser(null);
    }
  }, []);

  useEffect(() => {
    const init = async () => {
      try {
        const { data } = await insforge.auth.getSession();
        if (data.session?.user) {
          setUser(data.session.user as User);
        }
      } catch {
        setUser(null);
      } finally {
        setLoading(false);
      }
    };
    init();
  }, []);

  const signIn = useCallback(
    async (email: string, password: string) => {
      const { data, error } = await insforge.auth.signIn(email, password);
      if (error) return { error: error.message };
      setUser(data.user as User);
      router.push("/dashboard");
      return { error: null };
    },
    [router],
  );

  const signUp = useCallback(
    async (email: string, password: string, fullName?: string) => {
      const { data, error } = await insforge.auth.signUp(email, password, {
        name: fullName,
        full_name: fullName,
      });
      if (error) return { error: error.message };
      if (data.user) setUser(data.user as User);
      router.push("/dashboard");
      return { error: null };
    },
    [router],
  );

  const signOut = useCallback(async () => {
    await insforge.auth.signOut();
    setUser(null);
    router.push("/");
  }, [router]);

  return (
    <AuthContext.Provider
      value={{ user, loading, signIn, signUp, signOut, refreshUser }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
