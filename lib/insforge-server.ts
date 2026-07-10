import { cookies } from "next/headers";

const INSFORGE_URL = process.env.NEXT_PUBLIC_INSFORGE_URL!;

type ServerUser = {
  id: string;
  email: string;
  emailVerified?: boolean;
  providers?: string[];
  createdAt?: string;
  updatedAt?: string;
  profile?: {
    name?: string;
    avatar_url?: string;
    [key: string]: unknown;
  };
  metadata?: Record<string, unknown>;
};

type ServerSession = {
  accessToken: string;
  refreshToken: string;
  csrfToken: string | null;
  user: ServerUser;
};

async function insforgeServerRequest<T>(
  path: string,
  accessToken: string,
  options: RequestInit = {},
): Promise<T> {
  const headers: Record<string, string> = {
    Authorization: `Bearer ${accessToken}`,
    "Content-Type": "application/json",
    ...((options.headers as Record<string, string>) || {}),
  };

  const response = await fetch(`${INSFORGE_URL}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => null);
    throw new Error(
      errorBody?.message || errorBody?.error_description || `Request failed: ${response.status}`,
    );
  }

  return response.json();
}

async function getAccessToken(): Promise<string | null> {
  const cookieStore = await cookies();
  const sessionCookie = cookieStore.get("insforge-session");
  if (!sessionCookie) return null;

  try {
    const session = JSON.parse(sessionCookie.value) as ServerSession;
    return session.accessToken;
  } catch {
    return null;
  }
}

async function getUser(): Promise<{
  data: { user: ServerUser | null };
  error: { message: string } | null;
}> {
  const token = await getAccessToken();
  if (!token) {
    return { data: { user: null }, error: { message: "No session" } };
  }

  try {
    const result = await insforgeServerRequest<{ user: ServerUser }>(
      "/api/auth/sessions/current",
      token,
    );

    return { data: { user: result.user }, error: null };
  } catch {
    return { data: { user: null }, error: { message: "Failed to get user" } };
  }
}

type ServerQueryBuilder<T> = {
  select: (columns?: string) => ServerQueryBuilder<T>;
  eq: (column: string, value: unknown) => ServerQueryBuilder<T>;
  order: (
    column: string,
    options?: { ascending?: boolean },
  ) => ServerQueryBuilder<T>;
  single: () => Promise<{ data: T | null; error: { message: string } | null }>;
  limit: (count: number) => ServerQueryBuilder<T>;
  insert: (
    data: Record<string, unknown> | Record<string, unknown>[],
  ) => Promise<{ data: T | null; error: { message: string } | null }>;
  update: (data: Record<string, unknown>) => ServerQueryBuilder<T>;
  then: (
    resolve: (value: {
      data: T[] | null;
      error: { message: string } | null;
    }) => void,
  ) => void;
};

function from<T>(table: string): ServerQueryBuilder<T> {
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
    const token = await getAccessToken();
    if (!token) {
      return { data: null, error: { message: "Not authenticated" } };
    }

    try {
      if (state.operation === "insert") {
        const result = await insforgeServerRequest<T[]>(
          `/api/database/records/${table}`,
          token,
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

        const result = await insforgeServerRequest<T[]>(
          path,
          token,
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

      const result = await insforgeServerRequest<T[]>(path, token);
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

  const builder: ServerQueryBuilder<T> = {
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
  const token = await getAccessToken();
  if (!token) {
    return { data: { path: "" }, error: { message: "Not authenticated" } };
  }

  try {
    const strategyRes = await fetch(
      `${INSFORGE_URL}/api/storage/buckets/${bucket}/upload-strategy`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
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

export const createInsforgeServer = async () => {
  return {
    auth: { getUser },
    from,
    storage: { upload, getUrl },
  };
};
