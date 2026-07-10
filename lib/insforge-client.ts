const INSFORGE_URL = process.env.NEXT_PUBLIC_INSFORGE_URL!;
const INSFORGE_ANON_KEY = process.env.NEXT_PUBLIC_INSFORGE_ANON_KEY!;

type InsForgeProfile = {
  name?: string;
  avatar_url?: string;
  [key: string]: unknown;
};

type InsForgeUser = {
  id: string;
  email: string;
  emailVerified?: boolean;
  providers?: string[];
  createdAt?: string;
  updatedAt?: string;
  profile?: InsForgeProfile;
  metadata?: Record<string, unknown>;
};

type AuthResponse = {
  data: {
    user: InsForgeUser | null;
    session: { accessToken: string; refreshToken: string; csrfToken: string | null } | null;
  };
  error: { message: string; statusCode?: number; error?: string } | null;
};

type SessionData = {
  accessToken: string;
  refreshToken: string;
  csrfToken: string | null;
  user: InsForgeUser;
};

type InsForgeSignupResponse = {
  user: InsForgeUser;
  accessToken: string | null;
  csrfToken: string | null;
  refreshToken: string | null;
  requireEmailVerification?: boolean;
};

type InsForgeLoginResponse = {
  user: InsForgeUser;
  accessToken: string;
  csrfToken: string | null;
  refreshToken: string | null;
};

const AUTH_STORAGE_KEY = "insforge-auth";
const SESSION_KEY = "insforge-session";

function getStoredSession(): SessionData | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(SESSION_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as SessionData;
  } catch {
    return null;
  }
}

function setSessionCookie(session: SessionData | null): void {
  if (typeof document === "undefined") return;
  if (session) {
    document.cookie = `${AUTH_STORAGE_KEY}=${encodeURIComponent(JSON.stringify(session))}; path=/; max-age=${60 * 60 * 24 * 7}; SameSite=Lax`;
  } else {
    document.cookie = `${AUTH_STORAGE_KEY}=; path=/; max-age=0; SameSite=Lax`;
  }
}

function setStoredSession(session: SessionData | null): void {
  if (typeof window === "undefined") return;
  if (session) {
    localStorage.setItem(SESSION_KEY, JSON.stringify(session));
    localStorage.setItem(AUTH_STORAGE_KEY, "true");
  } else {
    localStorage.removeItem(SESSION_KEY);
    localStorage.removeItem(AUTH_STORAGE_KEY);
  }
  setSessionCookie(session);
}

async function insforgeRequest<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((options.headers as Record<string, string>) || {}),
  };

  const session = getStoredSession();
  if (session?.accessToken) {
    headers["Authorization"] = `Bearer ${session.accessToken}`;
  } else {
    headers["Authorization"] = `Bearer ${INSFORGE_ANON_KEY}`;
  }

  const response = await fetch(`${INSFORGE_URL}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => null);
    throw {
      message: errorBody?.message || errorBody?.error_description || `Request failed: ${response.status}`,
      statusCode: response.status,
      error: errorBody?.error,
    };
  }

  return response.json();
}

async function signInWithEmail(
  email: string,
  password: string,
): Promise<AuthResponse> {
  try {
    const result = await insforgeRequest<InsForgeLoginResponse>(
      "/api/auth/sessions",
      {
        method: "POST",
        body: JSON.stringify({ email, password }),
      },
    );

    if (!result.accessToken) {
      return {
        data: { user: result.user, session: null },
        error: { message: "No access token returned" },
      };
    }

    const session: SessionData = {
      accessToken: result.accessToken,
      refreshToken: result.refreshToken || "",
      csrfToken: result.csrfToken,
      user: result.user,
    };

    setStoredSession(session);

    return { data: { user: result.user, session }, error: null };
  } catch (error: unknown) {
    const err = error as { message?: string; statusCode?: number; error?: string };
    return {
      data: { user: null, session: null },
      error: {
        message: err?.message || "Sign in failed",
        statusCode: err?.statusCode,
        error: err?.error,
      },
    };
  }
}

async function signUpWithEmail(
  email: string,
  password: string,
  metadata?: { full_name?: string; name?: string },
): Promise<AuthResponse> {
  try {
    const body: Record<string, unknown> = { email, password };
    const name = metadata?.name || metadata?.full_name;
    if (name) body.name = name;

    const result = await insforgeRequest<InsForgeSignupResponse>(
      "/api/auth/users",
      {
        method: "POST",
        body: JSON.stringify(body),
      },
    );

    if (result.requireEmailVerification && !result.accessToken) {
      return {
        data: { user: result.user, session: null },
        error: null,
      };
    }

    if (!result.accessToken) {
      return {
        data: { user: result.user, session: null },
        error: { message: "Email verification required. Please check your inbox." },
      };
    }

    const session: SessionData = {
      accessToken: result.accessToken,
      refreshToken: result.refreshToken || "",
      csrfToken: result.csrfToken,
      user: result.user,
    };

    setStoredSession(session);

    return { data: { user: result.user, session }, error: null };
  } catch (error: unknown) {
    const err = error as { message?: string; statusCode?: number; error?: string };
    return {
      data: { user: null, session: null },
      error: {
        message: err?.message || "Sign up failed",
        statusCode: err?.statusCode,
        error: err?.error,
      },
    };
  }
}

async function signOut(): Promise<{ error: { message: string } | null }> {
  try {
    const session = getStoredSession();
    if (session?.accessToken) {
      await fetch(`${INSFORGE_URL}/api/auth/logout`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.accessToken}`,
        },
      }).catch(() => {});
    }
  } catch {
    // ignore logout errors
  }
  setStoredSession(null);
  return { error: null };
}

async function getSession(): Promise<{
  data: {
    session: SessionData | null;
  };
  error: { message: string } | null;
}> {
  const session = getStoredSession();
  return { data: { session }, error: null };
}

async function getUser(): Promise<{
  data: { user: InsForgeUser | null };
  error: { message: string } | null;
}> {
  const session = getStoredSession();
  if (!session?.accessToken) {
    return { data: { user: null }, error: { message: "No session" } };
  }

  try {
    const result = await insforgeRequest<{ user: InsForgeUser }>(
      "/api/auth/sessions/current",
    );
    return { data: { user: result.user }, error: null };
  } catch {
    return { data: { user: session?.user ?? null }, error: null };
  }
}

async function updateUser(
  attributes: { data?: Record<string, unknown>; email?: string; password?: string },
): Promise<AuthResponse> {
  try {
    const session = getStoredSession();
    if (!session) throw new Error("Not authenticated");

    const profileData: Record<string, unknown> = {};
    if (attributes.data) {
      Object.assign(profileData, attributes.data);
    }

    const result = await insforgeRequest<{ id: string; profile: InsForgeProfile }>(
      "/api/auth/profiles/current",
      {
        method: "PATCH",
        body: JSON.stringify({ profile: profileData }),
      },
    );

    const updatedUser: InsForgeUser = {
      ...session.user,
      profile: { ...session.user.profile, ...result.profile },
    };

    const updatedSession = { ...session, user: updatedUser };
    setStoredSession(updatedSession);

    return { data: { user: updatedUser, session: updatedSession }, error: null };
  } catch (error) {
    return {
      data: { user: null, session: null },
      error: { message: error instanceof Error ? error.message : "Update failed" },
    };
  }
}

type QueryBuilder<T> = {
  select: (columns?: string) => QueryBuilder<T>;
  eq: (column: string, value: unknown) => QueryBuilder<T>;
  order: (
    column: string,
    options?: { ascending?: boolean },
  ) => QueryBuilder<T>;
  single: () => Promise<{ data: T | null; error: { message: string } | null }>;
  limit: (count: number) => QueryBuilder<T>;
  insert: (
    data: Record<string, unknown> | Record<string, unknown>[],
  ) => Promise<{ data: T | null; error: { message: string } | null }>;
  update: (
    data: Record<string, unknown>,
  ) => QueryBuilder<T>;
  then: (
    resolve: (value: {
      data: T[] | null;
      error: { message: string } | null;
    }) => void,
  ) => void;
};

function from<T>(table: string): QueryBuilder<T> {
  const state: {
    selectCols: string;
    filters: [string, string, unknown][];
    orderCol: string | null;
    orderAsc: boolean;
    limitCount: number | null;
    operation: "select" | "insert" | "update";
    body: Record<string, unknown> | null;
  } = {
    selectCols: "*",
    filters: [],
    orderCol: null,
    orderAsc: true,
    limitCount: null,
    operation: "select",
    body: null,
  };

  const execute = async (): Promise<{
    data: T[] | null;
    error: { message: string } | null;
  }> => {
    try {
      if (state.operation === "insert") {
        const result = await insforgeRequest<T[]>(
          `/api/database/records/${table}`,
          {
            method: "POST",
            body: JSON.stringify(
              Array.isArray(state.body) ? state.body : [state.body],
            ),
          },
        );
        return { data: Array.isArray(result) ? result : [result], error: null };
      }

      if (state.operation === "update" && state.body) {
        let path = `/api/database/records/${table}`;
        if (state.filters.length > 0) {
          const eqFilters = state.filters
            .filter((f) => f[1] === "eq")
            .map((f) => `${f[0]}=eq.${f[2]}`)
            .join("&");
          path += `?${eqFilters}`;
        }

        const result = await insforgeRequest<T[]>(
          path,
          {
            method: "PATCH",
            body: JSON.stringify(state.body),
          },
        );
        return { data: Array.isArray(result) ? result : [result], error: null };
      }

      let path = `/api/database/records/${table}?select=${state.selectCols}`;

      for (const [col, op, val] of state.filters) {
        path += `&${col}=${op}.${val}`;
      }

      if (state.orderCol) {
        path += `&order=${state.orderCol}.${state.orderAsc ? "asc" : "desc"}`;
      }

      if (state.limitCount) {
        path += `&limit=${state.limitCount}`;
      }

      const result = await insforgeRequest<T[]>(path);
      return { data: result, error: null };
    } catch (error) {
      return {
        data: null,
        error: {
          message: error instanceof Error ? error.message : "Query failed",
        },
      };
    }
  };

  const builder: QueryBuilder<T> = {
    select: (columns?: string) => {
      state.selectCols = columns || "*";
      state.operation = "select";
      return builder;
    },
    eq: (column: string, value: unknown) => {
      state.filters.push([column, "eq", value]);
      return builder;
    },
    order: (column: string, options?: { ascending?: boolean }) => {
      state.orderCol = column;
      state.orderAsc = options?.ascending ?? true;
      return builder;
    },
    single: async () => {
      state.limitCount = 1;
      const result = await execute();
      return {
        data: result.data?.[0] ?? null,
        error: result.error,
      };
    },
    limit: (count: number) => {
      state.limitCount = count;
      return builder;
    },
    insert: (data: Record<string, unknown> | Record<string, unknown>[]) => {
      state.operation = "insert";
      state.body = data as Record<string, unknown>;
      return execute() as Promise<{ data: T | null; error: { message: string } | null }>;
    },
    update: (data: Record<string, unknown>) => {
      state.operation = "update";
      state.body = data;
      return builder;
    },
    then: (resolve: (value: { data: T[] | null; error: { message: string } | null }) => void) => {
      execute().then(resolve);
    },
  };

  return builder;
}

async function upload(
  bucket: string,
  path: string,
  file: File,
): Promise<{ data: { path: string }; error: { message: string } | null }> {
  try {
    const session = getStoredSession();
    if (!session?.accessToken) {
      return { data: { path: "" }, error: { message: "Not authenticated" } };
    }

    const strategyRes = await fetch(
      `${INSFORGE_URL}/api/storage/buckets/${bucket}/upload-strategy`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.accessToken}`,
        },
        body: JSON.stringify({ path, contentType: file.type }),
      },
    );

    if (!strategyRes.ok) {
      const err = await strategyRes.json().catch(() => null);
      throw new Error(err?.message || `Upload strategy failed: ${strategyRes.status}`);
    }

    const strategy = await strategyRes.json() as {
      uploadUrl: string;
      method: string;
      headers?: Record<string, string>;
    };

    const uploadHeaders: Record<string, string> = {
      ...strategy.headers,
    };
    if (file.type) {
      uploadHeaders["Content-Type"] = file.type;
    }

    const uploadRes = await fetch(strategy.uploadUrl, {
      method: strategy.method || "PUT",
      headers: uploadHeaders,
      body: file,
    });

    if (!uploadRes.ok) {
      throw new Error(`Upload failed: ${uploadRes.status}`);
    }

    return { data: { path: `${bucket}/${path}` }, error: null };
  } catch (error) {
    return {
      data: { path: "" },
      error: { message: error instanceof Error ? error.message : "Upload failed" },
    };
  }
}

function getUrl(bucket: string, path: string): string {
  return `${INSFORGE_URL}/api/storage/buckets/${bucket}/objects/${path}`;
}

export const insforge = {
  auth: {
    signIn: signInWithEmail,
    signUp: signUpWithEmail,
    signOut,
    getSession,
    getUser,
    updateUser,
  },
  from,
  storage: { upload, getUrl },
};
